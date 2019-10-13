import json
import collections
from time import time
from bson.objectid import ObjectId

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session
from auth.models import User
from chat.models import UnreadMessage


def redirect(request, router_name):
    url = request.app.router[router_name].url_for()
    raise web.HTTPFound(url)


def set_session(session, user_id, request):
    session['user'] = str(user_id)
    session['last_visit'] = time()
    redirect(request, 'main')

def convert_json(message):
    return json.dumps({'error': message})


class Login(web.View):

    @aiohttp_jinja2.template('auth/login.html')
    async def get(self):
        session = await get_session(self.request)
        if session.get('user'):
            redirect(self.request, 'main')
        return {'content': 'Please, enter login or e-mail'}

    async def post(self):
        data = await self.request.post()
        user = User(self.request.app.db, data)
        result = await user.check_user()
        if isinstance(result, dict):
            session = await get_session(self.request)
            set_session(session, str(result['_id']), self.request)
        else:
            return web.Response(content_type='application/json', text=convert_json(result))


class SignIn(web.View):

    @aiohttp_jinja2.template('auth/sign.html')
    async def get(self, **kw):
        # sesion = await get_session(self.request)
        # if session.get('user'):
        #     redirect(self.request, 'main')
        return {'content': 'Please, enter login and pass'}

    async def post(self, **kw):
        data = await self.request.post()
        user = User(self.request.app.db, data)
        result = await user.create_user()
        if isinstance(result, ObjectId):
            session = await get_session(self.request)
            set_session(session, str(result), self.request)
        else:
            return web.Response(content_type='application/json', text=convert_json(result))

class SignOut(web.View):

    async def get(self, **kw):
        session = await get_session(self.request)
        if session.get('user'):
            del session['user']
            redirect(self.request, 'login')
        else:
            raise web.HTTPForbidden(body=b'Forbidden')


class AccountDetails(web.View):

    @aiohttp_jinja2.template('auth/account.html')
    async def get(self, **kw):
        user = User(self.request.app.db, {})

        session = await get_session(self.request)
        self_id = session.get('user')
        login = await user.get_login(self_id)
        user.login = login
        account = await user.check_user()
        users = await user.get_all_users()

        unread = UnreadMessage(self.request.app.db)
        r_unread = await unread.get_messages_recieved(self_id)
        unread_counter = collections.Counter()
        for mes in r_unread:
            unread_counter[mes['from_user']] += 1

        context = {
            'users': users,
            'user': account,
            'unread_counter': unread_counter, 
        }
        return context

    async def post(self, **kw):
        user = User(self.request.app.db, {})

        data = await self.request.json()
        session = await get_session(self.request)
        self_id = session.get('user')
        login = await user.get_login(self_id)
        
        await user.update_user(self_id, data)
        return web.json_response({})
