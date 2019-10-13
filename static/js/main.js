$(document).ready(function(){
    var sock = {};

    var chat_name = $('#my-data').data().name
    var to_user = $('#my-data').data().to_user
    var to_user_login = $('#my-data').data().to_user_login
    var own_login = $('#my-data').data().own_login
    var self_id = $('#my-data').data().self_id
    var online_id = $('#my-data').data().online_id
    

    var counter = new Proxy({}, {
      get: (target, name) => name in target ? target[name] : 0
    })

    $('.btn_chat').each(function(){
        counter[this.id] = this.value
    })
    try{
        sock = new WebSocket('ws://' + window.location.host + '/ws?chat_name=' + $('#my-data').data().name);
    }
    catch(err){
        sock = new WebSocket('wss://' + window.location.host + '/ws?chat_name=' + $('#my-data').data().name);
    }

    // show message in div#subscribe
    function showMessage(message) {
        var messageElem = $('#subscribe'),
            height = 0,
            date = new Date(),
            options = { hour12: false },
            htmlText = '[' + date.toLocaleTimeString('en-US', options) + '] ';

        try{
            var messageObj = JSON.parse(message);
            if (messageObj.type == 'msg'){
                htmlText = `${htmlText}<span class="user">${messageObj.from}</span>: ${messageObj.msg}\n`;
                messageElem.append($('<p class="unread">').html(htmlText));
                
                if (messageObj.to_user == self_id){
                    c = ++counter[`user_${messageObj.from}`]
                    $(`#user_${messageObj.from}`).val(c)
                    $(`#user_${messageObj.from}`).removeClass('btn-success').addClass('btn-info')
                    $(`#user_${messageObj.from}`).text(`${messageObj.from} (${c})`)
                }

            } else if(messageObj.type == 'joined'){
                $(`#user_${messageObj.user}`).removeClass('btn-secondary').addClass('btn-success')

            } else if(messageObj.type == 'left'){
                $(`#user_${messageObj.user}`).removeClass('btn-success').addClass('btn-secondary')

            } else if(messageObj.type == 'read'){
                $('.unread').removeClass('unread')
            }
        } catch (e){
            console.log(e)
            htmlText = htmlText + message;
            messageElem.append($('<p>').html(htmlText));
        }
    }

    function sendMessage(){
        var msg = $('#message');
        sock.send(JSON.stringify({
            'msg': msg.val(),
            'chat_name': chat_name,
            'to_user': to_user,
            'to_user_login': to_user_login,
        }));
        msg.val('').focus();
    }

    function updateUnread(){
        if (counter[`user_${to_user_login}`] > 0){
            data = {
                'login': own_login,
                'self_id': self_id,
                'chat_name': chat_name,
                'to_user': to_user,
            }
            setTimeout(function(){
                $.ajax({
                    dataType: 'json',
                    url: 'http://0.0.0.0:8080/update',
                    type: 'POST',
                    data: JSON.stringify(data),
                    success: function(data) {
                        if (data){
                            $(`#user_${to_user_login}`).removeClass('btn-info').addClass('btn-success')
                        } else {
                            $(`#user_${to_user_login}`).removeClass('btn-info').addClass('btn-secondary')
                        }
                        $(`#user_${to_user_login}`).text(to_user_login)
                        counter[`user_${to_user_login}`] = 0
                    }
                });
            }, 200)
        }
    }

    sock.onopen = function(){
        console.log('Connection to server started');
        $("#messages_box").hover(() =>{
            updateUnread()
        })
    };

    // send message from form
    $('#submit').click(function() {
        sendMessage();
    });

    $('#message').keyup(function(e){
        if(e.keyCode == 13){
            sendMessage();
        }
    });

    // income message handler
    sock.onmessage = function(event) {
        showMessage(event.data);
    };

    $('#signout').click(function(){
        window.location.href = "signout";
    });

    sock.onclose = function(event){
        if(event.wasClean){
            showMessage('Clean connection end');
        }else{
            showMessage('Connection broken');
        }
    };

    sock.onerror = function(error){
        showMessage(error);
    };


});
