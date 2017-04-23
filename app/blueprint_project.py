from app import app, socketio
from flask import Blueprint, render_template, flash, redirect, request, url_for, session, abort, jsonify, make_response
from flask_socketio import emit, join_room, leave_room
from . import mailing
from . import forms
from . import userDAO
from .decorators import requireLoginLevel
from .functions import get_db
import logging
import string, random
import requests
from .crawl import getArticle
import datetime, calendar, time

logr = logging.getLogger('gimphub.blueprint_chan')
project_B = Blueprint('project', __name__)
from gridfs import GridFS
from .XCF import XCF
from .picture_change import getChanges


def get_gridfs():
    db = get_db()
    gf = GridFS(db)
    return gf


@project_B.route('/newProject', methods=['POST'])
def newProject():
    # room=request.args['room'] if 'room' in request.args else None

    if not 'user' in session:
        return jsonify({'ok': 0, 'err': 'Must log in to create project'})

    db = get_db()

    # user = db.users.find_one({'_id':session['user']})



    db.users.update({'_id': session['user']}, {'$addToSet': {'projects': [request.json['repoName']]}})
    db.projects.insert({'_id': "%s%s" % (session['user'], request.json['repoName']), 'images': []})

    return jsonify({'ok': 1})


@project_B.route('/<user>/<project>/getLiveImage', methods=['GET'])
def getLiveImage(user, project):
    db = get_db()
    GFS = get_gridfs()
    image = db.projects.find_one({'_id': "%s%s" % (user, project)},
                                 {'images': {'$slice': -1}})
    if image and 'images' in image and image['images']:
        GFS = get_gridfs()
        img = GFS.get(image['images'][0])
        XC = XCF.XCF()
        XC.load_image(img)
        f, l = XC.get_full_image_and_layers()
        response = make_response(f.read())
        response.headers['Content-Type'] = 'image/png'
        response.headers['Content-Disposition'] = 'attachment; filename=img.png'
        return response
    return ""


@project_B.route('/getHistory', methods=['POST'])
def getHistory():
    db = get_db()
    GFS = get_gridfs()
    images = db.projects.find_one({'_id': "%s%s" % (request.json['user'], request.json['project'])},
                                  {'images': {'$slice': -10}})
    if images and 'images' in images and images['images']:
        pngs = []
        for image in reversed(images['images']):
            img = GFS.get(image)
            XC = XCF.XCF()
            XC.load_image(img)
            f, l = XC.get_full_image_and_layers()
            pngs.append(f)

        print(pngs)
        finalOut = []
        for i, png in enumerate(pngs):
            if i < len(pngs) - 1:
                changes = getChanges(png, pngs[i + 1])
                finalOut.append(changes)

        print(finalOut)
        return jsonify({'ok': 1, 'something': finalOut})


@project_B.route('/uploadImage', methods=['POST', 'GET'])
def uploadImage():
    # room=request.args['room'] if 'room' in request.args else None
    print(request.form)
    print(request.files)

    if not request.files:
        return jsonify({'ok': 0, 'err': 'No file was selected'})

    imgFile = request.files['uploadFile']

    print(imgFile)

    GFS = get_gridfs()
    fileid = GFS.put(imgFile.read())
    db = get_db()
    db.projects.update({'_id': "%s%s" % (session['user'], request.form['projectName'])}, {'$push': {'images': fileid}})

    return redirect("/%s/%s" % (session['user'], request.form['projectName']))


@project_B.route('/<user>/<project>', methods=['GET'])
def project(user, project):
    # room=request.args['room'] if 'room' in request.args else None

    db = get_db()
    image = db.projects.find_one({'_id': "%s%s" % (user, project)}, {'images': {'$slice': -1}})
    if image and 'images' in image and image['images']:
        GFS = get_gridfs()
        img = GFS.get(image['images'][0])
        XC = XCF.XCF()
        XC.load_image(img)
        f, l = XC.get_full_image_and_layers()
    else:
        img = None

    return render_template('project.html', project=project, img=img)


# @project_B.route('/imgupdate', methods = ['POST'])
# def imgupdate():
#     #room=request.args['room'] if 'room' in request.args else None
#
#     print(request.form['update'])
#
#     if not all([x in request.form for x in ('project', 'user')]):
#         return jsonify({'ok':0})
#
#     emit('imgupdate', {'update': request.form['update']}, room='project')
#
#     return jsonify({'ok': 0})

@socketio.on('echo', namespace='/chat')
def imgupdate():
    print("ECHO")
    emit("echo2")


@socketio.on('imgpush', namespace='/chat')
def imgupdate(update, project, user):
    print("imgpush")

    # if not all([x in request.form for x in ('project', 'user')]):
    #     return jsonify({'ok': 0})
    # join_room(session['user'])
    # room = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))

    emit('imgupdate', {'update': update, 'user': user}, room=project)


@project_B.route('/getImgUpdates', methods=['POST'])
def getImgUpdates():
    # room=request.args['room'] if 'room' in request.args else None

    print(request.form['update'])

    if not all([x in request.form for x in ('project', 'user')]):
        return jsonify({'ok': 0})

    emit('imgupdate', {'update': request.form['update'], 'user': request.form['user']}, room=request.form['project'])

    return jsonify({'ok': 0})


@project_B.route('/changeUserName', methods=['POST', 'GET'])
def changeUserName():
    if all(x in request.form for x in ('g-recaptcha-response', 'userNameChange')):

        dictToSend = {'secret': '6Ldw_wkUAAAAAJFyh_Pmg1KKyM_1ta4Rwg3smpEY',
                      'response': request.form['g-recaptcha-response']}
        res = requests.get('https://www.google.com/recaptcha/api/siteverify',
                           params=dictToSend,
                           verify=True)
        if res.json()['success']:

            return jsonify({'ok': 1})
        else:
            return jsonify({'ok': 0})
    else:
        return jsonify({'ok': 0})


labels = {
    'US_News': 'US News',
    'World_News': 'World News',
    'Politics': 'Politics',

    'Technology': 'Technology',
    'Entertainment': 'Entertainment',
    'Business': 'Business',

    'Sports': 'Sports',

    'Memes': 'Memes'}


@project_B.route('/categories/<category>', methods=['GET'])
def categories(category):
    name = labels[category]

    # getting the time until switch
    interval = app.config['SWITCH_SECONDS']

    current_time = calendar.timegm(time.gmtime())
    remainingTime = interval - (current_time % interval)
    print(remainingTime)

    return render_template('categories.html', categoryName=name,
                           category=category,
                           remainingTime=remainingTime,
                           interval=interval)


@project_B.route('/testArticles', methods=['GET'])
def testArticles():
    db = get_db()
    for i in range(30):
        db.articles.insert({'url': 'http://stackoverflow.com/questions/%d' % (5584586 + i),
                            'title': 'test%d' % (5584586 + i),
                            'category': 'Technology'})

    return "OK"


@project_B.route('/getCurrentArticle', methods=['POST'])
def getCurrentArticle():
    if not 'category' in request.json:
        return jsonify({'ok': 0, 'err': 'Must provide category'})

    interval = app.config['SWITCH_SECONDS']

    current_time = calendar.timegm(time.gmtime())
    intervals_passed = current_time // interval

    db = get_db()
    article = db.articles.find({'category': request.json['category']}).sort([('$natural', 1)]).limit(1)
    if not article.count():
        return jsonify({'ok': 0, 'err': 'no articles!'})
    article = article[0]
    # print article

    if 'index' not in article:
        db.articles.update({'_id': article['_id']}, {'$set': {'index': intervals_passed}})

    elif 'index' in article and intervals_passed > article['index']:
        db.articles.remove({'_id': article['_id']})
        article = db.articles.find({'category': request.json['category']}).sort([('$natural', 1)]).limit(1)
        if not article.count():
            return jsonify({'ok': 0, 'err': 'no articles!'})
        article = article[0]
        db.articles.update({'_id': article['_id']}, {'$set': {'index': intervals_passed}})

    del article['_id']
    return jsonify({'ok': 1, 'article': article})


@project_B.route('/upload', methods=['POST'])
def upload():
    if not 'category' in request.json or not 'url' in request.json or not 'title' in request.json:
        return jsonify({'ok': 0, 'err': 'Must provide category'})

    category = request.json['category']
    url = request.json['url']
    title = request.json['title']
    if category and url and title:
        article = {'url': url,
                   'title': title,
                   'category': category}
        try:
            if 'title' not in article or not article['title'] or article['title'].isspace():
                article['title'] = getArticle.get_generic_title(article['url'])
        except:
            pass
        try:
            article['content'] = getArticle.get_generic_article(article['url'])
        except:
            pass
        try:
            article['img'] = getArticle.get_generic_image(article['url'])
        except:
            pass
        db = get_db()
        print(article)
        try:
            db.articles.insert(article)
        except Exception as e:
            print("unknown error: %s" % str(e))

    return jsonify({'ok': 1})


@socketio.on('connect')
def connect3():
    print("connected")
    # join_room(session['user'])
    # room = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))

    emit('connectConfirm')


@socketio.on('connect', namespace='/chat')
def connect2():
    # join_room(session['user'])
    # room = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))

    emit('connectConfirm')


# 'disconnected' is a special event
@socketio.on('disconnect')
def disconnected():
    pass


@socketio.on('userDisconnect', namespace='/chat')
def userDisconnect(user, room):
    # db = get_db()
    # db.msgs.insert({'room':room, 'user':user, 'left':True, 'time':tStamp})

    leave_room(room)
    emit('userDisconnect', {'ok': 1, 'user': user, 'room': room}, room=room)


@socketio.on('requestUpdate', namespace='/chat')
def getUpdate(project, layer):
    print('fsaf')
    emit('imageUpdate', {'ok': 1, 'updates': [(1, 2, 244, 231, 5),
                                              (2, 1, 24, 231, 5),
                                              (3, 9, 244, 21, 5),
                                              (0, 2, 24, 231, 25), ]},
         room=project)


@socketio.on('joined', namespace='/chat')
def joined(user, project):
    join_room(project)
    # at some point, twisted will be implemented instead of this
    # loggedIn.addUser(user)
    # print loggedIn.getUsers()
    # db = get_db()
    # db.msgs.insert({'room':room, 'user':user, 'joined':True, 'time':tStamp})

    print('user joined')
    emit('joined', {'ok': 1, 'user': user, 'room': project}, room=project)


# @socketio.on('checkUsersOnlineInit', namespace='/chat')
# def checkUsersOnlineInit():
#     emit('checkUsersOnlineInit', {}, broadcast=True)
#
# @socketio.on('checkUsersOnlineConfirm', namespace='/chat')
# def checkUsersOnlineConfirm(user, status):
#     db = get_db()
#     #cur = [msg for msg in db.msgs.find({'room':status, 'msg':{'$exists':True}},{'_id':0}).sort([('$natural',-1)]).limit(20)]
#     cur = []
#     emit('checkUsersOnlineConfirm', {'msgs':cur, 'user':user, 'room':status}, room=room)

@socketio.on('chatMsg', namespace='/chat')
def chatMsg(user, room, data):
    # #msgs.insert({'post':message})
    # if message != 'connected':
    #
    #     msgsCol.insert({'user':message['user'], 'msg':message['post']})
    #
    #     emit('update', message, broadcast=True)
    # db = get_db()
    # db.msgs.insert({'room':room, 'user':user, 'msg':data})
    emit('chatMsg', {'user': user, 'data': data, 'room': room}, room=room)
