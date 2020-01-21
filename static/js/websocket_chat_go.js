$(document).ready(function(){
    var sock = {};

    var chat_name        = $('#my-data').data().name
    var company          = $('#chat-data').data().company
    // var to_user = $('#my-data').data().to_user
    // var to_user_login = $('#my-data').data().to_user_login
    var own_login        = $('#my-data').data().own_login
    var self_id          = $('#my-data').data().self_id
    // var online_id        = $('#my-data').data().online_id.split('#')
    var last_mess_author = $('#my-data').data().last_mess_author
    var company_id       = $('#my-data').data().company_id

    var c_id = company_id
    var type = 'company_chat_mess'
    var msg  = $('#message');
    var have_next_mess_part = true

    // var unread_counter = $('#chat-data').data().unread_counter
    var counter = new Proxy({}, {
      get: (target, name) => name in target ? target[name] : 0
    })

    var first_time = true

    // $('.btn_chat').each(function(){
    //     counter[this.id] = this.value
    //     if (this.value > 0){
    //         $(`#${this.id}`).removeClass('btn-secondary').addClass('btn-info')
    //         // $(`#${this.id}`).text(`${this.id.slice(4)} (${this.value})`)
    //     } else if ($.inArray(this.id.slice(5), online_id) != -1){
    //         console.log($(`#${this.id}`))
    //         $(`#${this.id}`).removeClass('btn-secondary').addClass('btn-success')
    //     }
    // })

    try{
        sock = new WebSocket(`ws://localhost:8081/go/ws_chat`);
    }
    catch(err){
        sock = new WebSocket(`wss://localhost:8081/go/ws_chat`);
    }

    // if (typeof company_id === "undefined"){
    //     try{
    //         sock = new WebSocket('ws://' + window.location.host + '/ws?chat_name=' + chat_name);
    //     }
    //     catch(err){
    //         sock = new WebSocket('wss://' + window.location.host + '/ws?chat_name=' + chat_name);
    //     }
    // } else {
    //     try{
    //         sock = new WebSocket('ws://' + window.location.host + '/ws_company?company_id=' + company_id);
    //     }
    //     catch(err){
    //         sock = new WebSocket('wss://' + window.location.host + '/ws_company?company_id=' + company_id);
    //     }
    // }

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
            if (messageObj.type == 'chat_mess'){
                htmlText = `${htmlText}<span class="user">${messageObj.from}</span>: ${messageObj.msg}\n`;

                // проверяем находимся ли мы в комнате общего чата, для которой сообщение
                if (typeof company_id !== 'null' && messageObj.company_id == company_id){
                    console.log(1)
                    if (self_id != messageObj.from_id){
                        c = ++counter['main']
                        $('#main_chat').val(c)
                        $('#main_chat').removeClass('btn-outline-success').addClass('btn-outline-info')
                        $('#main_chat').text(`Общий (${c})`)
                    }
                    messageElem.append($('<p class="unread">').html(htmlText));
                    scrollDown()
                // если сообщение из общего чата, но мы в другой комнате
                } else if (typeof company_id !== 'null') {
                    console.log(2)
                    c = ++counter['main']
                    $('#main_chat').val(c)
                    $('#main_chat').removeClass('btn-outline-success').addClass('btn-outline-info')
                    $('#main_chat').text(`Общий (${c})`)
                // если сообщение из приватного чата и мы находимся с ним в чате
                } else if (messageObj.from_id == to_user && chat_name == messageObj.chat_name){
                    console.log(3)
                    c = ++counter[`user_${messageObj.from_id}`]
                    $(`#user_${messageObj.from_id}`).val(c)
                    $(`#user_${messageObj.from_id}`).removeClass('btn-success').addClass('btn-info')
                    $(`#user_${messageObj.from_id}`).text(`${messageObj.from} (${c})`)
                    messageElem.append($('<p class="unread">').html(htmlText));
                // сообщение из приватного чата и мы не с ним в комнате
                } else {
                    console.log(4)
                    c = ++counter[`user_${messageObj.from_id}`]
                    $(`#user_${messageObj.from_id}`).val(c)
                    $(`#user_${messageObj.from_id}`).removeClass('btn-success').addClass('btn-info')
                    $(`#user_${messageObj.from_id}`).text(`${messageObj.from} (${c})`)
                }

                last_mess_author = messageObj.from_id


            // ообщение о том, что человек вошел в онлайн
            } else if(messageObj.type == 'joined'){
                    console.log(5)
                $(`#user_${messageObj.user_id}`).removeClass('btn-secondary').addClass('btn-success')

            // сообщение, что человек вышел из онлайна
            } else if(messageObj.type == 'left'){
                    console.log(6)
                $(`#user_${messageObj.user_id}`).removeClass('btn-success').addClass('btn-secondary')

            // сообщение, что человек прочел сообщение
            } else if(messageObj.type == 'read'){
                    console.log(7)
                if (messageObj.company_id == company_id){
                    counter['main'] = 0
                    $('#main_chat').val(0)
                    $('#main_chat').removeClass('btn-info').addClass('btn-outline-success')
                    $('#main_chat').text(`Общий`)
                    $('.unread').removeClass('unread')
                // } else if (messageObj.user_id == to_user){
                //     counter[`user_${to_user}`] = 0
                //     $(`#user_${to_user}`).val(0)
                //     $(`#user_${to_user}`).removeClass('btn-info').addClass('btn-success')
                //     $(`#user_${to_user}`).text(to_user_login)
                //     $('.unread').removeClass('unread')
                } else if (last_mess_author == self_id) {
                    $('.unread').removeClass('unread')
                }

            // Обработка оповещений
            } else if(messageObj.type == 'notification'){
                    console.log(8)

                    console.log(messageObj)
                text = messageObj.text
                if (text.length > 50) {
                    text = text.slice(0, 50) + '..."'
                }
                if (messageObj.subtype == 'new_mess') {
                    $('#notifications').text(text)
                } else if (messageObj.subtype == 'new_event') {
                    $('#notifications').text(text)
                } else if (messageObj.subtype == 'unread') {
                    $('.unread').removeClass('unread')
                }

            // Пачки сообщений при инициализации или прогрузке новых
            } else if(messageObj.type == 'part'){
                    console.log(9)
                messages = messageObj.messages
                if (messages) {
                    $('#last_mess').removeAttr("id")
                    have_next_mess_part = messages.length == 20 ? true : false
                    for (let i = 0;i < messages.length; i++) {
                        // попадает ли сообщение в непрочитанные
                        unread = i < messageObj.unr_count ? 'unread' : ''
                        // если сообщение последнее и есть еще сообщения на сервере (предположительно)
                        avail_old_mess = (i == 19 && have_next_mess_part) ? 'id="last_mess"' : ''

                        pattern = `
                            <p ${avail_old_mess} class="${unread} chat_mess">[${messages[i].InsertTime.split('T')[1].split('.')[0]}]
                                <span class="user">${messages[i].UserName}</span>: ${messages[i].Msg}
                            </p>
                        `
                         $("#subscribe").prepend(pattern);
                    }
                    set_upload_old_mess()
                    
                } else {
                    have_next_mess_part = false
                }

                if (first_time) {
                    scrollDown()
                    first_time = false
                    if (messages) {
                        last_mess_author = messages[0].FromUser
                    }
                }
            }
        } catch (e){
            console.log(e)
            htmlText = htmlText + message;
            messageElem.append($('<p>').html(htmlText));
        }
    }

    function sendMessage(){
        let data = {
            // 'from_client': true,
            'msg': msg.val(),
            'company': company,
            // 'to_user': to_user,
            // 'to_user_login': to_user_login,
            'company_id': company_id,
            'type': 'chat_mess',
            'from': self_id,
            'from_login': own_login,
        }
        sock.send(JSON.stringify(data));
        msg.val('').focus();
    }

    // function updateUnread(){
    //     if (counter[`user_${to_user}`] > 0){
    //         data = {
    //             'from_user': to_user,
    //         }
    //         setTimeout(function(){
    //             $.ajax({
    //                 dataType: 'json',
    //                 url: '/update',
    //                 type: 'POST',
    //                 data: JSON.stringify(data),
    //                 success: function(data) {
    //                     if (data){
    //                         $(`#user_${to_user}`).removeClass('btn-info').addClass('btn-success')
    //                     } else {
    //                         $(`#user_${to_user}`).removeClass('btn-info').addClass('btn-secondary')
    //                     }
    //                     $(`#user_${to_user}`).text(to_user_login)
    //                     counter[`user_${to_user}`] = 0
    //                     $('.unread').removeClass('unread')
    //                 }
    //             });
    //         }, 2000)
    //     }
    // }

    function updateUnreadInCompany(){

        if (counter['main'] > 0 && company_id && last_mess_author != self_id){
            data = {
                'company_id': company_id,
                'from': self_id,
                'type': 'unread'
            }
            sock.send(JSON.stringify(data));
            // setTimeout(function(){
            //     $.ajax({
            //         dataType: 'json',
            //         url: '/update_unread_company',
            //         type: 'POST',
            //         data: JSON.stringify(data),
            //         success: function(data) {
            //             $(`#main_chat`).removeClass('btn-outline-info').addClass('btn-outline-success')
            //             $(`#main_chat`).text('Общий')
            //             counter['main'] = 0
            //             $('.unread').removeClass('unread')
            //         }
            //     });
            // }, 200)
        }
    }

    sock.onopen = function(){
        sock.send(JSON.stringify({
            'company_id': company_id,
            'self_id': self_id,
            'login': own_login,
        }));
        console.log('Connection to server started');
        $("#messages_box").hover(() =>{
            updateUnreadInCompany()
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

    function set_upload_old_mess() {
        var $win = $('#subscribe');
        var $marker = $('#last_mess');

        if ($marker) {
            //отслеживаем событие прокрутки страницы
            $win.scroll(function() {
              if($win.scrollTop() <= $marker.offset().top) {
                console.log('Viden')
                sock.send(JSON.stringify({
                    'company_id': company_id,
                    'self_id': self_id,
                    'login': own_login,
                    'type': 'part',
                }));
              }else{
                console.log('Ne Viden')
              }
            });
        }
    }

    // $('.btn_chat').click(function(){
    //     let user_id = this.id.slice(5)
    //     let user_login = this.name
    //     data = {
    //         'user_id': user_id
    //     }
    //     $.ajax({
    //         dataType: 'json',
    //         url: '/user_chat',
    //         type: 'POST',
    //         data: JSON.stringify(data),
    //         success: function(data) {
    //             result = ''
    //             to_user = user_id
    //             chat_name = data['chat_name']
    //             to_user_login = user_login
    //             messages = data.messages
    //             company_id = null
    //             last_mess_author = data.last_mess_author
    //             for (mess of messages){
    //                 cls = mess['unread'] ? 'unread' : ''
    //                 let html_p = `<p class=${cls}>[${mess['time']}]<span class="user"> ${mess['from_user']}</span>: ${mess['msg']}</p>`
    //                 result += html_p
    //             }
    //             $('#subscribe').html(result)
    //             $(`#user_${user_id}`).text(user_login)
    //             $('#chat_with').text(`Чат с ${user_login}`)
    //             counter[`user_${user_id}`] = 0
    //             if (data['is_online']){
    //                 $(`#user_${user_id}`).removeClass('btn-info').addClass('btn-success')
    //             } else {
    //                 $(`#user_${user_id}`).removeClass('btn-info').addClass('btn-secondary')
    //             }
    //             $("#messages_box").hover(() =>{
    //                 updateUnread()
    //             });
    //             type = 'private_chat_mess'
    //         }
    //     });
    // });

    // $('#main_chat').click(function(){
    //     data = {
    //         'company_id': c_id
    //     }
    //     $.ajax({
    //         dataType: 'json',
    //         url: '/user_chat_company',
    //         type: 'POST',
    //         data: JSON.stringify(data),
    //         success: function(data) {
    //             result = ''
    //             to_user = ''
    //             chat_name = ''
    //             to_user_login = ''
    //             company_id = c_id

    //             messages = data.messages
    //             last_mess_author = data.last_mess_author
    //             for (mess of messages){
    //                 cls = mess['unread'] ? 'unread' : ''
    //                 let html_p = `<p class=${cls}>[${mess['time']}]<span class="user"> ${mess['from_user']}</span>: ${mess['msg']}</p>`
    //                 result += html_p
    //             }
    //             $('#subscribe').html(result)
    //             $('#chat_with').text('Общий чат')
    //             $("#messages_box").hover(() =>{
    //                 updateUnreadInCompany()
    //             });
    //             type = 'company_chat_mess'
    //         }
    //     });
    // });

    sock.onclose = function(event){
        let data = {
            'type': 'closed',
        }
        sock.send(JSON.stringify(data));

        if(event.wasClean){
            showMessage('Clean connection end');
        }else{
            showMessage('Connection broken');
        }
    };

    sock.onerror = function(error){
        showMessage(error);
    };

    function scrollDown() { 
        var div = $("#subscribe");
        div.scrollTop(10000);
    }


});