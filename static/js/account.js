$(document).ready(function(){

    $('#signin').click(function(){
        window.location.href = "signin";
    });

    function showError(error){
        $('#success').html('');
        $('#error').html(error);
    }
    function showSucces(){
        $('#error').html('');
        $('#success').html('Данные успешно измененны.');
    }

    $('#submit').click(function(){
        errors = ''
        invalid_fields = []
        $(':invalid').each(function(){
            invalid_fields.push(this.id)
        })
        if ($.inArray( 'login', invalid_fields) != -1){
            errors += 'Неверный формат логина.<br>'
        }
        if ($.inArray( 'email', invalid_fields) != -1){
            errors += 'Неверный формат e-mail.<br>'
        }
        if ($.inArray( 'password', invalid_fields) != -1){
            errors += 'Неверный формат пароля.<br>'
        }
        if ($.inArray( 'name', invalid_fields) != -1){
            errors += 'Неверный формат имени.<br>'
        }
        if ($.inArray( 'sername', invalid_fields) != -1){
            errors += 'Неверный формат фамилии.<br>'
        }
        if ($('#password').val() != $('#confirm_password').val()){
            errors += 'Пароли не совпадают.<br>'
        }
        showError(errors)
        if (errors){
            return
        }
        var new_data = {
            'login': $('#login').val(),
            'password': $('#password').val(),
            'name': $('#name').val(),
            'sername': $('#sername').val(),
            'email': $('#email').val(),
            'bday': $('#bday').val(),
        }
        $.post('account', JSON.stringify(new_data), function(data){
            if (data.error){
                showError(data.error);
            }else{
                showSucces();
                if (data['login'] != ''){
                    $('#login_label').text(new_data['login'])
                }
                if (data['name'] != ''){
                    $('#name_label').text(new_data['name'])
                }
                if (data['sername'] != ''){
                    $('#sername_label').text(new_data['sername'])
                }
                if (data['email'] != ''){
                    $('#email_label').text(new_data['email'])
                }
                if (data['bday'] != ''){
                    $('#ebday_label').text(new_data['bday'])
                }


            }
        });
    });
});
