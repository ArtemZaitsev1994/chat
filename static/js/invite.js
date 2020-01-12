$(document).ready(function(){

    var company_id = $('#company-data').data().company_id

    function showError(error){
        $('#success').html('');
        $('#error').html(error);
    }
    function showSucces(){
        $('#error').html('');
        $('#success').html('Тусовка создана.');
    }

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
