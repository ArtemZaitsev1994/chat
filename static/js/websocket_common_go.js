$(document).ready(function(){
    try{
        sock = new WebSocket('ws://localhost:8081/go/ws_common');
    }
    catch(err){
        sock = new WebSocket('wss://localhost:8081/go/ws_common');
    }

    sock.onopen = function(){
        console.log('Common connection to GO-server started');
    };

    // income message handler
    sock.onmessage = function(event) {
        console.log(event.data);
    };

    sock.onclose = function(event){
        console.log('Closed');
    };

    sock.onerror = function(error){
        console.log(error);
    };


});
