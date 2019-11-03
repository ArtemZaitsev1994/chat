$(document).ready(function(){

    var company_id = $('#company-data').data().company_id
    // var self_id = $('#my-data').data().self_id
    // var own_login = $('#my-data').data().own_login

    function showError(error){
        $('#success').html('');
        $('#error').html(error);
    }
    function showSucces(){
        $('#error').html('');
        $('#success').html('ТусЭ создана.');
    }

    $('#accept').on('click', () => {
        if ($('#password').length && $('#password').val() == ''){
            showError('Введите пароль')
            return
        }
        data = {
            'company_id': company_id
        }
        if ($('#password').length){
            data['password'] = $('#password').val()
        }
        console.log(data)
        $.ajax({
            dataType: 'json',
            url: '/company',
            type: 'POST',
            data: JSON.stringify(data),
            success: function(data) {
                if (data.error){
                    showError(data.error)
                } else {
                    location.reload();
                }
            }
        });
    })
    $('#quit').on('click', () => {
        data = {
            'company_id': company_id
        }
        $.ajax({
            dataType: 'json',
            url: '/my_companys',
            type: 'DELETE',
            data: JSON.stringify(data),
            success: function(data) {
                if (data){
                     location.reload();
                } else {
                    showError('Ошибка на стороне сервера')
                }
            }
        });

    })
    $('#delete').on('click', () => {
        console.log(1)
        data = {
            'company_id': company_id
        }
        $.ajax({
            dataType: 'json',
            url: '/company',
            type: 'DELETE',
            data: JSON.stringify(data),
            success: function(data) {
                if (data){
                     window.location.replace("/all_companys");
                } else {
                    showError('Ошибка на стороне сервера')
                }
            }
        });

    })
    $('.accept_inv').on('click', function() {
        user_id = this.getAttribute('user_id')
        data = {
            'user_id': user_id,
            'company_id': company_id,
            'type': true,
        }
        $.ajax({
            dataType: 'json',
            url: '/invite',
            type: 'PUT',
            data: JSON.stringify(data),
            success: function(data) {
                if (data){
                     $(`#inv_${user_id}`).html('<p style="{color: green}">Принят</p>')
                 } else {
                    showError('Ошибка на стороне сервера')
                }
            }
        });

    })
    $('.decline_inv').on('click', function() {
        user_id = this.getAttribute('user_id')
        data = {
            'user_id': user_id,
            'company_id': company_id,
            'type': false,
        }

        $.ajax({
            dataType: 'json',
            url: '/invite',
            type: 'PUT',
            data: JSON.stringify(data),
            success: function(data) {
                if (data){
                     $(`#inv_${user_id}`).html('<p style="{color: red}">Отклонен</p>')
                } else {
                    showError('Ошибка на стороне сервера')
                }
            }
        });

    })
});
