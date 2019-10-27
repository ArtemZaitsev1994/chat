$(document).ready(function(){
    var sock = {};

    var unread_counter = $('#chat-data').data().unread_counter

    var chat_name = $('#my-data').data().name
    var to_user = $('#my-data').data().to_user
    var to_user_login = $('#my-data').data().to_user_login
    var own_login = $('#my-data').data().own_login
    var self_id = $('#my-data').data().self_id
    var online_id = $('#my-data').data().online_id.split('#')
    var company_id = $('#my-data').data().company_id
    var c_id = company_id
    

    var counter = new Proxy({}, {
      get: (target, name) => name in target ? target[name] : 0
    })

    $('.btn_chat').each(function(){
        counter[this.id] = this.value
        console.log(online_id)
        console.log(this.id.slice(5))
        console.log($.inArray(this.id.slice(5), online_id) != -1)
        if (this.value > 0){
            $(`#${this.id}`).removeClass('btn-secondary').addClass('btn-info')
            // $(`#${this.id}`).text(`${this.id.slice(4)} (${this.value})`)
        } else if ($.inArray(this.id.slice(5), online_id) != -1){
            console.log($(`#${this.id}`))
            $(`#${this.id}`).removeClass('btn-secondary').addClass('btn-success')
        }
    })
    counter['main'] = $('#main_chat').val()

    if (typeof company_id === "undefined"){
        try{
            sock = new WebSocket('ws://' + window.location.host + '/ws?chat_name=' + chat_name);
        }
        catch(err){
            sock = new WebSocket('wss://' + window.location.host + '/ws?chat_name=' + chat_name);
        }
    } else {
        try{
            sock = new WebSocket('ws://' + window.location.host + '/ws_company?company_id=' + company_id);
        }
        catch(err){
            sock = new WebSocket('wss://' + window.location.host + '/ws_company?company_id=' + company_id);
        }
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
            // если пришло сообщение с текстом
            if (messageObj.type == 'msg'){
                htmlText = `${htmlText}<span class="user">${messageObj.from}</span>: ${messageObj.msg}\n`;

                // проверяем находимся ли мы в комнате, для которой сообщение
                if (typeof messageObj.company_id !== 'null' && messageObj.company_id == company_id){
                    c = ++counter['main']
                    $('#main_chat').val(c)
                    $('#main_chat').removeClass('btn-outline-success').addClass('btn-outline-info')
                    $('#main_chat').text(`Общий (${c})`)
                    messageElem.append($('<p class="unread">').html(htmlText));
                } else if (messageObj.from_id == to_user){
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

    function sendMessage(){
        var msg = $('#message');
        sock.send(JSON.stringify({
            'msg': msg.val(),
            'chat_name': chat_name,
            'to_user': to_user,
            'to_user_login': to_user_login,
            'company_id': company_id,
        }));
        msg.val('').focus();
    }

    function updateUnread(){
        if (counter[`user_${to_user}`] > 0
                || (counter['main'] > 0 && company_id)){
            data = {
                'from_user': to_user,
                'company_id': company_id,
            }
            setTimeout(function(){
                $.ajax({
                    dataType: 'json',
                    url: '/update',
                    type: 'POST',
                    data: JSON.stringify(data),
                    success: function(data) {
                        if (data){
                            $(`#user_${to_user}`).removeClass('btn-info').addClass('btn-success')
                        } else {
                            $(`#user_${to_user}`).removeClass('btn-info').addClass('btn-secondary')
                        }
                        $(`#user_${to_user}`).text(to_user_login)
                        counter[`user_${to_user}`] = 0
                        console.log(1)
                        $('.unread').removeClass('unread')
                    }
                });
            }, 200)
        }
    }

    sock.onopen = function(){
        console.log('Connection to server started');
        $("#messages_box").hover(() =>{
            updateUnread()
        });
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

    $('.btn_chat').click(function(){
        let user_id = this.id.slice(5)
        let user_login = this.name
        data = {
            'user_id': user_id
        }
        $.ajax({
            dataType: 'json',
            url: '/user_chat',
            type: 'POST',
            data: JSON.stringify(data),
            success: function(data) {
                result = ''
                to_user = user_id
                chat_name = data['chat_name']
                to_user_login = user_login
                messages = data.messages
                company_id = null
                for (mess of messages){
                    cls = mess['unread'] ? 'unread' : ''
                    let html_p = `<p class=${cls}>[${mess['time']}]<span class="user"> ${mess['from_user']}</span>: ${mess['msg']}</p>`
                    result += html_p
                }
                $('#subscribe').html(result)
                $(`#user_${user_id}`).text(user_login)
                $('#chat_with').text(`Чат с ${user_login}`)
                counter[`user_${user_id}`] = 0
                if (data['is_online']){
                    $(`#user_${user_id}`).removeClass('btn-info').addClass('btn-success')
                } else {
                    $(`#user_${user_id}`).removeClass('btn-info').addClass('btn-secondary')
                }
            }
        });
    });

    $('#main_chat').click(function(){
        data = {
            'company_id': c_id
        }
        $.ajax({
            dataType: 'json',
            url: '/user_chat_company',
            type: 'POST',
            data: JSON.stringify(data),
            success: function(data) {
                result = ''
                to_user = ''
                chat_name = ''
                to_user_login = ''
                company_id = c_id

                messages = data.messages
                for (mess of messages){
                    cls = mess['unread'] ? 'unread' : ''
                    let html_p = `<p class=${cls}>[${mess['time']}]<span class="user"> ${mess['from_user']}</span>: ${mess['msg']}</p>`
                    result += html_p
                }
                $('#subscribe').html(result)
                $('#chat_with').text('Общий чат')
            }
        });
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
