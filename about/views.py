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
