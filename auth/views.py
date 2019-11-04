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
            redirect(self.request, 'account')
        return {'is_socket': False}

    async def post(self):
        data = await self.request.post()
        user = User(self.request.app.db, data)
        result = await user.check_user()
        if isinstance(result, dict):
            session = await get_session(self.request)
            set_session(session, str(result['_id']), user.login, self.request)
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
            set_session(session, str(result), user.login, self.request)
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
        session = await get_session(self.request)
        self_id = session.get('user')
        login = session.get('login')
        user = self.request.app['models']['user']
        company = self.request.app['models']['company']


        user_id = self.request.rel_url.query.get('id')
        if user_id:
            account = await user.get_user(user_id)
            access = user_id == self_id
            users_company = await company.get_companys_by_user(user_id)
            own_user_company = await company.get_own_companys(user_id)
        else:
            users_company = await company.get_companys_by_user(self_id)
            own_user_company = await company.get_own_companys(self_id)
            account = await user.get_user(self_id)
            access = True

        context_data = {
            'user': account,
            'own_login': login,
            'is_socket': True,
            'self_id': self_id,
            'access': access,
            'own_companys': own_user_company,
            'companys': users_company,
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
