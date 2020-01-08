$(document).ready(function(){
    var sock = {};

    var company_id = $('#my-data').data().company_id
    var own_login  = $('#my-data').data().own_login
    var self_id    = $('#my-data').data().self_id

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
                    text = `${text.slice(0, 50)}...`
                }
                if (messageObj.subtype == 'new_mess') {
                    $('#notifications').text(`Новое сообщение в чате ${messageObj.company} от ${messageObj.from} "${text}"`)
                } else if (messageObj.subtype == 'new_event') {
                    $('#notifications').text(messageObj.text)
                }
                console.log(`Notification - message: ${messageObj.msg}\nfrom: ${messageObj.from}`)
            }
        } catch (e){
            console.log(e)
            htmlText = htmlText + message;
            messageElem.append($('<p>').html(htmlText));
        }
    }

    sock.onopen = function(){
        data = {
            'company_id': company_id,
            'self_id': self_id,
            'login': own_login,
        }
        console.log(data)
        sock.send(JSON.stringify(data));
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
            console.log('Clean connection end');
        }else{
            console.log('Connection broken');
        }
    };

    sock.onerror = function(error){
        showMessage(error);
    };


});