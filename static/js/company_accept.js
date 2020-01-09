$(document).ready(function(){

    var company_id = $('#my-data').data().company_id
    var self_id    = $('#my-data').data().self_id
    var own_login  = $('#my-data').data().own_login

    console.log(company_id)
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
        console.log(data)
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
                     window.location.replace("/news");
                } else {
                    showError('Ошибка на стороне сервера')
                }
            }
        });

    })
    $('#invitation').on('click', () => {
        if ($('#note').length > 0){
            data = {
                'company_id': company_id,
                'note': $('#note').val()
            }

            $.ajax({
                dataType: 'json',
                url: '/invite',
                type: 'POST',
                data: JSON.stringify(data),
                success: function(data) {
                    if (data){
                         $('#invitation').text('Отменить запрос')
                         $('#invitation_data').html(`<p style="color: green">Запрос отправлен. Статус: Ожидает</p>`)
                     } else {
                        showError('Ошибка на стороне сервера')
                    }
                }
            });

        } else {

            data = {
                'company_id': company_id
            }

            $.ajax({
                dataType: 'json',
                url: '/invite',
                type: 'DELETE',
                data: JSON.stringify(data),
                success: function(data) {
                    if (data){
                         $('#invitation').text('Отправить запрос на вступление')
                         $('#invitation_data').html(`
                            <div class="input-group">
                              <div class="input-group-prepend">
                                <span class="input-group-text">Записка админу</span>
                              </div>
                              <textarea class="form-control" id='note' aria-label="With textarea"></textarea>
                            </div>`)
                    } else {
                        showError('Ошибка на стороне сервера')
                    }
                }
            });
        }

    })
});
