$(document).ready(function(){

    var socket = io.connect('http://' + document.domain + ':' + location.port + '/' + 'chat', {});
    //var user = makeid() + '-user';
    var onlineUsers = [];
    var awayUsers = [];
   // var room = category;
    var room = project;

    console.log(project);


    $('#uploadFileBtn').click(function () {
        $('#uploadFileForm').submit();
    });

    var imgX;
    var imgY;

    sendJS({'user':user, 'project':project}, "getHistory", function(r){
        console.log(r);

        for(var timepoint in r['something']) {
            var outHTML = '<section><div class="col-md-4">' +
                '<h3>Added</h3><canvas id="hist-a-{0}"></canvas>'.format(timepoint) +
                '</div><div class="col-md-4"><h3>Removed</h3><canvas id="hist-d-{0}"></canvas>'.format(timepoint) +
                '</div><div class="col-md-4"><h3>Difference</h3><canvas id="hist-r-{0}"></canvas>'.format(timepoint) +
                '</div></section>';
            $('#history').append(outHTML);
            var $canvas = $("#hist-a-{0}".format(timepoint))[0],
                context = $canvas.getContext("2d");
            $canvas.height = imgY;
            $canvas.width = imgX;
            for (var i = 0, arr = r['something'][timepoint]['a']; i < arr.length; i++) {
                context.fillStyle = "rgb(" + arr[i][0] + "," + arr[i][1] + "," + arr[i][2] + ")";
                context.fillRect(arr[i][4], arr[i][5], 1, 1);
            }
            $canvas = $("#hist-d-{0}".format(timepoint))[0],
                context = $canvas.getContext("2d");
            $canvas.height = imgY;
            $canvas.width = imgX;
            for (i = 0, arr = r['something'][timepoint]['d']; i < arr.length; i++) {
                context.fillStyle = "rgb(" + arr[i][0] + "," + arr[i][1] + "," + arr[i][2] + ")";
                context.fillRect(arr[i][4], arr[i][5], 1, 1);
            }
            $canvas = $("#hist-r-{0}".format(timepoint))[0],
                context = $canvas.getContext("2d");
            $canvas.height = imgY;
            $canvas.width = imgX;
            for (i = 0, arr = r['something'][timepoint]['r']; i < arr.length; i++) {
                context.fillStyle = "rgb(" + arr[i][0] + "," + arr[i][1] + "," + arr[i][2] + ")";
                context.fillRect(arr[i][4], arr[i][5], 1, 1);
            }
        }
    });


    $('#tmpUser').text(user);

    socket.emit('connect');
    socket.on('connectConfirm', function(msg) {

    });

    $('#testbtn').click(function(){
        socket.emit('requestUpdate', project, 1);
    },
    function(){$(this).fadeOut(500).fadeIn(500); // fades button out then in
    })

    var $canvas = $("#canvas")[0],
        context = $canvas.getContext("2d");



    //sets canvas dimensions according to image
    var img = new Image();

    img.onload = function(){
        $canvas.height = img.height;
        $canvas.width = img.width;
        imgX = img.width;
        imgY = img.height;
        context.drawImage(img, 0, 0)
    }

    img.src =  "{0}/getLiveImage".format(project);



    //draws image pixel by pixel

    socket.on('imgupdate', function(update){
        console.log("got update");
        for(var i = 0, arr = update["update"] ; i < arr.length; i++){


        context.fillStyle = "rgb(" + arr[i][2] + "," + arr[i][3] + "," +arr[i][4] +")";
        context.fillRect(arr[i][1],arr[i][0],1,1);




        }
    })

     //builds an html list from an array of images
    socket.emit('joined', user, project);
    var $dispArea = $("#awesomediv");

    function listhistory(images){

        var imglist = '<ul>';

        for(var i = 0; i <images.length; i++){
             imglist += '<li class= \'imglist\' >' + '<img src = \' ' + images[i][0] + '\' >';
             imglist += '<img src = \' ' + images[i][1] + '\' >';
             imglist += '<p>after edit(left) vs before edit(right)</p>';
             imglist += '</li>';
           }
        imglist +='</ul>';

        $dispArea.html(imglist);

    }


    window.onbeforeunload = function() {
        socket.emit('userDisconnect', user, room);
    }

    socket.on('joined', function(msg) {

        console.log("client has joined! room {0} (self) user {1}".format(msg['room'], msg['user']));


    });



    // socket.on('chatMsg', function(msg){
    //     console.log('reply');
    //     console.log(msg);
    //     if(msg['room'] == room){
    //         var chatBox = $('#chatbox .textoutput');
    //         if(chatBox){
    //             chatBox.append("{0}: {1}\n".format(msg['user'], msg['data']));
    //             chatBox[0].scrollTop = chatBox[0].scrollHeight;
    //         }else{
    //             console.log("Message Received for non-existent chatbox {0}".format(msg['room']))
    //         }
    //     }
    // });

    // $(document).ready(function () {
    //     $('#userNameChangeForm').on('submit', function(e) {
    //         user = $('#userNameChange').val();
    //         $('#tmpUser').text(user);
    //         e.preventDefault();
    //         $.ajax({
    //             url : $(this).attr('action') || window.location.pathname,
    //             type: "POST",
    //             data: $(this).serialize(),
    //             success: function (data) {
    //                 console.log('success');
    //                 console.log(data);
    //                 if(data['ok']){
    //                     $('#userNameChangeRow').fadeOut(500);
    //                     socket.emit('joined', user, room);
    //                     setupChatBoxEvents($('#chatbox'));
    //                 }else{
    //                     $('#userNameChangeError').text("Error!");
    //                 }
    //                 //$("#form_output").html(data);
    //             },
    //             error: function (jXHR, textStatus, errorThrown) {
    //                 console.log('failure');
    //                 console.log(errorThrown);
    //                 $('#userNameChangeError').text("Error!");
    //                 //alert(errorThrown);
    //             }
    //         });
    //     });
    // });

    // socket.on('changedStatus', function(msg) {
    //     if(msg['status'] == 'away' && isInArray(msg['user'], onlineUsers)){
    //         var index = onlineUsers.indexOf(msg['user']);
    //         onlineUsers.splice(index, 1);
    //         awayUsers.push(msg['user']);
    //     }else if(msg['status'] == 'online' && isInArray(msg['user'], awayUsers)){
    //         var index = awayUsers.indexOf(msg['user']);
    //         awayUsers.splice(index, 1);
    //         onlineUsers.push(msg['user']);
    //     }
    //     updateUsersStatus();
    // });

    // socket.on('checkUsersOnlineInit', function(msg) {
    //     socket.emit('checkUsersOnlineConfirm', user,  room);
    // });

    // socket.emit('checkUsersOnlineInit');
    // socket.on('checkUsersOnlineConfirm', function(msg) {
    //     if(msg['mode'] == 'staff'){
    //         if(msg['status'] == 'online' && !isInArray(msg['user'], onlineUsers)){
    //             onlineUsers.push(msg['user']);
    //         }else if(msg['status'] == 'away' && !isInArray(msg['user'], awayUsers)){
    //             awayUsers.push(msg['user']);
    //         }
    //     }
    //     updateUsersStatus();
    // });
    //
    // function setupChatBoxEvents(chatbox){
    //     var button = chatbox.find('.chatsendbtn');
    //     button.unbind();
    //     button.click(function(){
    //         sendChatMsgHandler(chatbox);
    //     });
    //     var inputline = chatbox.find('.chatmsginput');
    //     inputline.unbind();
    //     inputline.keypress(function(e){
    //         if(e.which == 13) {
    //             e.preventDefault();
    //             sendChatMsgHandler(chatbox);
    //         }
    //     });
    //     $('#chatmsginput').show();
    //     $('#chatsendbtn').show();
    // }
    //
    // function sendChatMsgHandler(chatbox){
    //     var data = chatbox.find('.chatmsginput').val();
    //     console.log(data);
    //     socket.emit('chatMsg', user, room, data);
    //     chatbox.find('.chatmsginput').val('');
    // }

});

