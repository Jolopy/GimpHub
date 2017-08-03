#!/usr/bin/env python

from socketIO_client import SocketIO, BaseNamespace
from gimpfu import *
import os
import time
from threading import Thread
from array import array
import requests
import configparser
import websocket
import _thread
import http.client
import numpy as np



class GimpHubImage(object):

    def __init__(self, drawable):
        self.currentImage = self.get_pix()
        self.drawable = drawable
        self.update_suspended = False

    def set_pix(self, x, y, r, g, b):
        pdb.gimp_drawable_set_pixel(self.drawable, y, x, 3, [r, g, b])

    def split_img_evenly(self, n):
        activeImage, layer, tm, tn = self._get_active_image()
        vertical = layer.height / n

        srcRgn = layer.get_pixel_rgn(0, 0, layer.width, layer.height,
                                     False, False)
        # not done

    def get_pix(self):
        activeImage, layer, tm, tn = self._get_active_image()
        srcRgn = layer.get_pixel_rgn(0, 0, layer.width, layer.height,
                                     False, False)
        src_pixels = array("B", srcRgn[0:layer.width, 0:layer.height])
        imageArr = []
        index = 0
        for x in range(layer.width):
            row = []
            for y in range(layer.height):
                row.append(src_pixels[index:index+3])
                index += 3
            imageArr.append(row)
        print(src_pixels)
        return imageArr

    def get_changes(self):

        activeImage, layer, tm, tn = self._get_active_image()
        changes = []

        srcRgn = layer.get_pixel_rgn(0, 0, layer.width, layer.height,
                                     False, False)

        src_pixels = array("B", srcRgn[0:layer.width, 0:layer.height])

        verificationArray = []
        changes = []

        outerIndex = 0

        print("---------------------------------------------------")

        while True:

            if outerIndex % 2 == 0:
                changes = []
                workingArr = changes
            else:
                verificationArray = []
                workingArr = verificationArray
            index = 0
            for x in range(layer.width):
                #row = []
                for y in range(layer.height):
                    #row.append(src_pixels[index:index + 3])

                    # Save the value in the channel layers.
                    # print "(%s, %s) : (%r, %r, %r)" % (x, y, pixelR, pixelG, pixelB)

                    if self.currentImage[x][y] != src_pixels[index:index + 3]:
                        workingArr.append((x, y, src_pixels[index],
                                              src_pixels[index+1],
                                              src_pixels[index+2]))

                    index += 3
            outerIndex += 1

            if changes == verificationArray:
                for change in changes:
                    self.currentImage[change[0]][change[1]] = array('B', change[2:5])
                break
            time.sleep(2)

        return changes


    def _get_active_image(self):
        activeImage = gimp.image_list()[0]
        layer = pdb.gimp_image_get_active_layer(activeImage)



        # Calculate the number of tiles.
        tn = int(layer.width / 64)
        if (layer.width % 64 > 0):
            tn += 1
        tm = int(layer.height / 64)
        if (layer.height % 64 > 0):
            tm += 1

        return activeImage, layer, tm, tn

    def _get_img_pixels(self):

        activeImage, layer, tm, tn = self._get_active_image()

        imageArr = []


        # Iterate over the tiles.
        for i in range(tn):

            for j in range(tm):
                # Get the tiles.
                tile = layer.get_tile(False, j, i)

                # Iterate over the pixels of each tile.
                for x in range(tile.ewidth):
                    row = []
                    for y in range(tile.eheight):
                        # Get the pixel and separate his colors.
                        pixel = tile[x, y]
                        pixelR = pixel[0] + "\x00\x00"
                        pixelG = "\x00" + pixel[1] + "\x00"
                        pixelB = "\x00\x00" + pixel[2]

                        # If the image has an alpha channel (or any other channel) copy his values.
                        if (len(pixel) > 3):
                            for k in range(len(pixel) - 3):
                                pixelR += pixel[k + 3]
                                pixelG += pixel[k + 3]
                                pixelB += pixel[k + 3]

                        # Save the value in the channel layers.
                        #print "(%s, %s) : (%r, %r, %r)" % (x, y, pixelR, pixelG, pixelB)
                        row.append([pixelR, pixelG, pixelB])
                    imageArr.append(row)

        #print imageArr

        return imageArr

class ChatNamespace(BaseNamespace):

    def on_aaa_response(self, *args):
        print('on_aaa_response', args)

class GimpHubLive(object):

    def __init__(self, drawable, user):
        #config = ConfigParser.ConfigParser()
        #config.readfp(open(os.path.join(os.path.realpath(__file__), 'gimphub.ini')))
        self.drawable = drawable
        self.project = 'test2'
        #self.user = 'paul@gmail.com'
        self.user = user
        #self.remote_server = "gimphub.duckdns.org"
        self.remote_server = 'localhost'
        self.remote_port = '5000'
        self.lockfile_path = '/tmp/GHLIVE_LOCK_%s' % self.user
        if os.path.exists(self.lockfile_path):
            os.remove(self.lockfile_path)

        #websocket.enableTrace(True)
        self.running = True

        self.socketIO = SocketIO(self.remote_server, self.remote_port)
        self.socketIO.emit('connect')

        self.chatNamespace = self.socketIO.define(ChatNamespace, '/chat')

        self.chatNamespace.on('imgupdate', self.on_update)
        self.chatNamespace.on('joined', self.on_joined)
        self.chatNamespace.on('echo2', self.on_echo)

        self.chatNamespace.emit('joined', self.user, self.project)
        self.chatNamespace.emit('connect')


        Thread(target=self.run_th).start()

        time.sleep(2)
        self.chatNamespace.emit('echo')
        #

    def on_update(self, obj):
        print("UPDATE")
        print(obj['user'] != self.user)
        if obj['user'] != self.user and hasattr(self, 'GHIMG'):
            self.GHIMG.update_suspended = True
            for px in obj['update']:
                #print px
                self.GHIMG.set_pix(px[0], px[1], px[2], px[3], px[4])
            pdb.gimp_drawable_update(self.drawable, 0, 0, self.drawable.width, self.drawable.height)
            pdb.gimp_displays_flush()
            self.GHIMG.update_suspended = False


    def on_echo(self, *args):
        print("ECHO")

    def on_joined(self, *args):
        print("JOINED")
        print(args)

    def run_th(self):
        while True:
            self.socketIO.wait(seconds=10)
            if self.running is False:
                print("SOCKETIO DISCONNECT")
                self.socketIO.disconnect()
                break

    #
    # def run_ws_th(self):
    #     self.ws.run_forever()

    def send_update(self, update):

        self.chatNamespace.emit('imgpush', update, self.project, self.user)
        #
        # url = "http://%s:%s/imgupdate" % (self.remote_server, self.remote_port)
        # data = {'update': [list(x) for x in update], 'user':self.user, 'project':self.project}
        # print data
        # r = requests.post(url, data=data)
        # print r
    #
    # def ws_on_message(self, ws, message):
    #     print message
    #
    # def ws_on_error(self, ws, error):
    #     print error
    #
    # def ws_on_close(self, ws):
    #     print "### closed ###"
    #
    # def ws_on_open(self, ws):
    #     def run(*args):
    #         ws.send("joined", self.user, self.project)
    #         while True:
    #             time.sleep(1)
    #             if self.running is False:
    #                 ws.close()
    #                 print "thread terminated"
    #                 return None
    #         #    ws.send("Hello %d" % i)
    #     thread.start_new_thread(run, ())



    def __del__(self):
        try:
            if os.path.exists(self.lockfile_path):
                os.remove(self.lockfile_path)
        except:
            pass

    def start_live(self):

        self.GHIMG = GimpHubImage(self.drawable)

        while True:

            if os.path.exists(self.lockfile_path):
                print("CLIENT PROCESS ENDED")
                self.running = False
                os.remove(self.lockfile_path)
                break

            time.sleep(4)
            update = self.GHIMG.get_changes()
            print(len(update))
            if update:
                try:
                    self.send_update(update)
                except Exception as e:
                    print("Can not POST to server! : %s " % str(e))




def gimphub_live_DEV(img, drawable):
    t1 = GimpHubImage(drawable)

    for i in range(5):
        time.sleep(1)
        print(t1.get_pix())



def gimphub_live(img, drawable):

    imgProc = GimpHubLive(drawable, "user1")
    imgProc.start_live()

def gimphub_live_2(img, drawable):

    imgProc = GimpHubLive(drawable, "user2")
    imgProc.start_live()


def gimphub_live_end(img, drawable):
    lockfile_path = '/tmp/GHLIVE_LOCK_%s' % "user1"
    if os.path.exists(lockfile_path):
        print("Already shutting down!")
        return None
    with open(lockfile_path, 'w'):
        pass

def gimphub_live_end_2(img, drawable):
    lockfile_path = '/tmp/GHLIVE_LOCK_%s' % "user2"
    if os.path.exists(lockfile_path):
        print("Already shutting down!")
        return None
    with open(lockfile_path, 'w'):
        pass

def gimphub_test_px(img, drawable):
    g = GimpHubImage(drawable)
    g.set_pix(2, 2, 100, 100, 100)

register("gimphub-livestart_DEV", "", "", "", "", "",
  "<Image>/Image/DEV", "RGB, RGB*",
  [
             # (PF_STRING, "arg0", "argument 0", "test string"),
  ],
  [],
  gimphub_live_DEV
  )

# register("gimphub-livestart", "", "", "", "", "",
#   "<Image>/Image/Activate Gimphub", "RGB, RGB*",
#   [
#              # (PF_STRING, "arg0", "argument 0", "test string"),
#   ],
#   [],
#   gimphub_live
#   )
#
# register("gimphub-livestart2", "", "", "", "", "",
#   "<Image>/Image/Activate Gimphub (2)", "RGB, RGB*",
#   [
#              # (PF_STRING, "arg0", "argument 0", "test string"),
#   ],
#   [],
#   gimphub_live_2
#   )
#
# register("gimphub-liveend", "", "", "", "", "",
#   "<Image>/Image/End Gimphub", "RGB, RGB*",
#   [
#              # (PF_STRING, "arg0", "argument 0", "test string"),
#   ],
#   [],
#   gimphub_live_end
#   )
#
# register("gimphub-liveend2", "", "", "", "", "",
#   "<Image>/Image/End Gimphub (2)", "RGB, RGB*",
#   [
#              # (PF_STRING, "arg0", "argument 0", "test string"),
#   ],
#   [],
#   gimphub_live_end_2
#   )
#
# register("gimphub-asf", "", "", "", "", "",
#   "<Image>/Image/GH TEST", "RGB, RGB*",
#   [
#              # (PF_STRING, "arg0", "argument 0", "test string"),
#   ],
#   [],
#   gimphub_test_px
#   )

main()
