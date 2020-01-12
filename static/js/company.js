$(document).ready(function(){

    function showError(error){
        $('#success').html('');
        $('#error').html(error);
    }
    function showSucces(){
        $('#error').html('');
        $('#success').html('Тусовка создана.');
    }

    $('#private').on('change', () => {
        if ($('#private').prop('checked')){
            $('#password').removeAttr('disabled')
            $('#confirm_password').removeAttr('disabled')
        } else {
            $('#password').attr('disabled', '')
            $('#confirm_password').attr('disabled', '')

        }
    })

    $('#submit').click(function(){
        errors = ''
        invalid_fields = []
        $(':invalid').each(function(){
            invalid_fields.push(this.id)
        })
        if ($.inArray( 'name', invalid_fields) != -1){
            errors += 'Неверный формат имени.<br>'
        }
        if ($.inArray( 'about', invalid_fields) != -1){
            errors += 'Заполните поле "о Тусовке".<br>'
        }
        if ($('#private').prop('checked')){
            if ($.inArray( 'password', invalid_fields) != -1){
                errors += 'Неверный формат пароля.<br>'
            }
            if ($('#password').val() != $('#confirm_password').val()){
                errors += 'Пароли не совпадают.<br>'
            } 
        }
        showError(errors)
        if (errors){
            return
        }
        var new_data = {}
        new_data['name'] = $('#name').val()
        new_data['about'] = $('#about').val()
        if ($('#private').prop('checked')){
            new_data['private'] = true
            new_data['password'] = $('#password').val()
        } else {
            new_data['private'] = false
        }
        $.post('my_companys', JSON.stringify(new_data), function(data){
            if (data.error){
                showError(data.error);
            }else{
                showSucces();
            }
        });
    });

    $('#my_companys').on('click', function() {
        console.log(this)
        $(`#create_block`).css('display', 'none')
        $('#companys').css('display', 'block')
    })
    $('#create_company').on('click', function() {
        $('#create_block').css('display', 'block')
        $(`#companys`).css('display', 'none')
    })
});
