$(document).ready(function(){
    var sock = {};
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
                htmlText = `${htmlText}<span class="user">${messageObj.user}</span>: ${messageObj.msg}\n`;
                messageElem.append($('<p>').html(htmlText));
            } else if(messageObj.type == 'joined'){
                $(`#user_${messageObj.user}`).removeClass('btn-outline-secondary').addClass('btn-success')
            } else if(messageObj.type == 'left'){
                $(`#user_${messageObj.user}`).removeClass('btn-success').addClass('btn-outline-secondary')
            }
        } catch (e){
            htmlText = htmlText + message;
            messageElem.append($('<p>').html(htmlText));
        }

        messageElem.find('p').each(function(i, value){
            height += parseInt($(this).height());
        });
        messageElem.animate({scrollTop: height});
    }

    function sendMessage(){
        var msg = $('#message');
        let chat_name = $('#my-data').data().name
        sock.send(JSON.stringify({'msg': msg.val(), 'chat_name': chat_name}));
        msg.val('').focus();
    }

    sock.onopen = function(){
        console.log('Connection to server started');
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
