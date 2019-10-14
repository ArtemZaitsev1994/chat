import json
import collections
import aiohttp_jinja2
from time import time
from bson.objectid import ObjectId
from aiohttp import web
from aiohttp_session import get_session

from auth.models import User
from utils import get_context
from auth.utils import redirect, set_session, convert_json


class Login(web.View):

    @aiohttp_jinja2.template('auth/login.html')
    async def get(self):
        session = await get_session(self.request)
        if session.get('user'):
            redirect(self.request, 'main')
        return {'is_socket': False}

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
        return {'is_socket': False}

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
    @get_context
    async def get(self, data, **kw):
        data['user'].login = data['login']
        account = await data['user'].check_user()

        context_data = {
            'users': data['users'],
            'own': account,
            'unread_counter': data['unread_counter'],
            'own_login': data['login'],
            'is_socket': True,
            'online': data['online_id'],
            'self_id': data['self_id']
        }
        return context_data

    async def post(self, **kw):
        user = User(self.request.app.db, {})

        data = await self.request.json()
        session = await get_session(self.request)
        self_id = session.get('user')
        login = await user.get_login(self_id)
        await user.update_user(self_id, data)
        return web.json_response({})
