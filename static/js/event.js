$(document).ready(function(){

    var company_id = $('#my-data').data().company_id

    function showError(error){
        $('#success').html('');
        $('#error').html(error);
    }
    function showSucces(){
        $('#error').html('');
        $('#success').html('Ивент создан.');
    }

    $.urlParam = function(name){
        var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
        if (results==null) {
           return null;
        }
        return decodeURI(results[1]) || 0;
    }

    

    $('#submit').click(function(){
        errors = ''
        invalid_fields = []
        $(':invalid').each(function(){
            invalid_fields.push(this.id)
        })
        if ($.inArray( 'name', invalid_fields) != -1){
            errors += 'Неверный формат имени.<br>'
        }
        if ($.inArray('date', invalid_fields) != -1){
            errors += 'Введите дату. <br>'
        } else {
            date = $('#date').val().split('-')
            date[1] -= 1
            time = []
            if ($('#time').val() != ''){
                time = $('#time').val().split(':')
            }
            event_date = new Date(...date.concat(time))
            today = new Date()
            if (event_date < today){
                errors += 'Дата не может быть в прошлом'
            }   
        }
        showError(errors)
        if (errors){
            return
        }
        var new_data = {}
        new_data['name'] = $('#name').val()
        new_data['about'] = $('#about').val()
        new_data['date'] = $('#date').val()
        if ($('#time').val() != ''){
            new_data['time'] = $('#time').val()
        }
        new_data['private'] = $('#private').prop('checked')
        new_data['company_id'] = company_id
        console.log(new_data)
        $.post('event', JSON.stringify(new_data), function(data){
            if (data.error){
                showError(data.error);
            }else{
                showSucces();
            }
        });
    });
});
