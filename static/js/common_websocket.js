$(document).ready(function(){
    try{
        sock = new WebSocket('ws://' + window.location.host + '/ws_common');
    }
    catch(err){
        sock = new WebSocket('wss://' + window.location.host + '/ws_common');
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
            console.log(messageObj)
            console.log(chat_name)
            // если пришло сообщение с текстом
            if (messageObj.type == 'msg'){
                htmlText = `${htmlText}<span class="user">${messageObj.from}</span>: ${messageObj.msg}\n`;

                // проверяем находимся ли мы в комнате, для которой сообщение
                if (typeof company_id !== 'null' && messageObj.company_id == company_id){
                    console.log(3)
                    c = ++counter['main']
                    $('#main_chat').val(c)
                    $('#main_chat').removeClass('btn-outline-success').addClass('btn-outline-info')
                    $('#main_chat').text(`Общий (${c})`)
                    messageElem.append($('<p class="unread">').html(htmlText));
                } else if (messageObj.from_id == to_user && chat_name == messageObj.chat_name){
                    console.log(4)
                    c = ++counter[`user_${messageObj.from_id}`]
                    $(`#user_${messageObj.from_id}`).val(c)
                    $(`#user_${messageObj.from_id}`).removeClass('btn-success').addClass('btn-info')
                    $(`#user_${messageObj.from_id}`).text(`${messageObj.from} (${c})`)
                    messageElem.append($('<p class="unread">').html(htmlText));
                }
                else if (messageObj.from_id == self_id) {

                } else {
                    c = ++counter[`user_${messageObj.from_id}`]
                    $(`#user_${messageObj.from_id}`).val(c)
                    $(`#user_${messageObj.from_id}`).removeClass('btn-success').addClass('btn-info')
                    $(`#user_${messageObj.from_id}`).text(`${messageObj.from} (${c})`)
                }


            // ообщение о том, что человек вошел в онлайн
            } else if(messageObj.type == 'joined'){
                $(`#user_${messageObj.user_id}`).removeClass('btn-secondary').addClass('btn-success')

            // сообщение, что человек вышел из онлайна
            } else if(messageObj.type == 'left'){
                $(`#user_${messageObj.user_id}`).removeClass('btn-success').addClass('btn-secondary')

            // сообщение, что человек прочел сообщение
            } else if(messageObj.type == 'read'){
                if (messageObj.company_id == company_id){
                    counter['main'] = 0
                    $('#main_chat').val(0)
                    $('#main_chat').removeClass('btn-info').addClass('btn-outline-success')
                    $('#main_chat').text(`Общий`)
                    $('.unread').removeClass('unread')
                } else if (messageObj.user_id == to_user){
                    counter[`user_${to_user}`] = 0
                    $(`#user_${to_user}`).val(0)
                    $(`#user_${to_user}`).removeClass('btn-info').addClass('btn-success')
                    $(`#user_${to_user}`).text(to_user_login)
                    $('.unread').removeClass('unread')
                }
            }
        } catch (e){
            console.log(e)
            htmlText = htmlText + message;
            messageElem.append($('<p>').html(htmlText));
        }
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
