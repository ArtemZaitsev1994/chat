$(document).ready(function(){
    var sock = {};

    var chat_name        = $('#my-data').data().name
    var company          = $('#my-data').data().company
    // var to_user = $('#my-data').data().to_user
    // var to_user_login = $('#my-data').data().to_user_login
    var own_login        = $('#my-data').data().own_login
    var self_id          = $('#my-data').data().self_id
    var online_id        = $('#my-data').data().online_id.split('#')
    var last_mess_author = $('#my-data').data().last_mess_author
    var company_id       = $('#my-data').data().company_id

    var c_id = company_id
    var type = 'company_chat_mess'
    var msg  = $('#message');

    var unread_counter = $('#chat-data').data().unread_counter
    var counter = new Proxy({}, {
      get: (target, name) => name in target ? target[name] : 0
    })

    $('.btn_chat').each(function(){
        counter[this.id] = this.value
        if (this.value > 0){
            $(`#${this.id}`).removeClass('btn-secondary').addClass('btn-info')
            // $(`#${this.id}`).text(`${this.id.slice(4)} (${this.value})`)
        } else if ($.inArray(this.id.slice(5), online_id) != -1){
            console.log($(`#${this.id}`))
            $(`#${this.id}`).removeClass('btn-secondary').addClass('btn-success')
        }
    })
    counter['main'] = $('#main_chat').val()

    try{
        sock = new WebSocket(`ws://localhost:8081/go/ws_common`);
    }
    catch(err){
        sock = new WebSocket(`wss://localhost:8081/go/ws_common`);
    }

    // show message in div#subscribe
    function showMessage(message) {
        var messageElem = $('#subscribe'),
            height = 0,
            date = new Date(),
            options = { hour12: false },
            htmlText = '[' + date.toLocaleTimeString('en-US', options) + '] ';

        try{
            console.log(message)
            var messageObj = JSON.parse(message);
            if(messageObj.type == 'notification'){
                text = messageObj.text
                if (text.length > 50) {
                    text = text.slice(0, 50) + '...'
                }
                if (messageObj.subtype == 'new_mess') {
                    $('#notifications').text(`Новое сообщение в чате ${messageObj.company} от ${messageObj.from} "${text}"`)
                }
                console.log(`Notification - message: ${messageObj.msg}\nfrom: ${messageObj.from}`)
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
        console.log(data)
        sock.send(JSON.stringify(data));
        msg.val('').focus();
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

    // income message handler
    sock.onmessage = function(event) {
        console.log("sock.onmessage:\n", event.data)
        showMessage(event.data);
    };

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


});