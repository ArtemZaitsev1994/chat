$(document).ready(function(){

    function showError(error){
        $('#success').html('');
        $('#error').html(error);
    }
    function showSucces(){
        $('#error').html('');
        $('#success').html('E-mail отправлен.');
    }

    $('#submit').click(function(){
        
        var new_data = {}
        new_data['callback'] = $('#callback').val()
        new_data['message'] = $('#message').val()
        $.post('about', JSON.stringify(new_data), function(data){
            if (data.error){
                showError(data.error);
            }else{
                showSucces();
            }
        });
    });
});
