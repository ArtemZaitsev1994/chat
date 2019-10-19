import aiohttp_jinja2
import collections
from aiohttp import web
from aiohttp_session import get_session

from auth.models import User
from chat.models import UnreadMessage
from utils import get_context


class About(web.View):
    @aiohttp_jinja2.template('about/about.html')
    @get_context
    async def get(self, data, **kw):

        photo_path = 'photo/main.gif'

        context = {
            'users': data['users'],
            'own_login': data['login'],
            'photo_path': photo_path,
            'unread_counter': data['unread_counter'],
            'is_socket': True,
            'self_id': data['self_id']
        }
        return context


async def drop_all(request):
    from auth.models import User
    from chat.models import Message, UnreadMessage
    from company.models import Company
    from events.models import Event, Photo

    models = {
        'user': User(request.app.db, {}),
        'chat': Message(request.app.db),
        'unread': UnreadMessage(request.app.db),
        'event': Event(request.app.db),
        'company': Company(request.app.db),
        'photo': Photo(request.app.db),
    }
    [await i.clear_db() for i in models.values()]

    leo = User(request.app.db, {'login': 'Leo', 'email': 'leo@mail.ru', 'password': 'qwe123'})
    lana = User(request.app.db, {'login': 'Lana', 'email': 'delRay@mail.ru', 'password': 'qwe123'})
    artem = User(request.app.db, {'login': 'Artem', 'email': 'artz1994@mail.ru', 'password': 'qwe123'})
    await leo.create_user()
    await lana.create_user()
    await artem.create_user()



