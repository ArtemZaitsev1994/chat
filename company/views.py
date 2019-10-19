import json
import collections
import aiohttp_jinja2
from time import time
from bson.objectid import ObjectId
from aiohttp import web
from aiohttp_session import get_session

from auth.models import User
from company.models import Company as comp_model
from utils import get_context, get_companys_context
from auth.utils import redirect, set_session, convert_json


class MyCompany(web.View):

    @aiohttp_jinja2.template('company/my_companys.html')
    @get_companys_context
    async def get(self, data):
        session = await get_session(self.request)
        login = session.get('login')
        data.update({'is_socket': False, 'own_login': login})
        return data

    async def post(self, **kw):
        company = comp_model(self.request.app.db)

        data = await self.request.json()
        session = await get_session(self.request)
        self_id = session.get('user')
        login = session.get('login')
        if await company.create_company(data, self_id):
            return web.json_response(True)
        return web.json_response({'error': 'ТусЭ уже есть.'})
    
    async def delete(self, **kw):
        data = await self.request.json()
        session = await get_session(self.request)
        self_id = session.get('user')
        company = comp_model(self.request.app.db)
        user = User(self.request.app.db, {})

        result = await company.delete_user_from_comp(data['company_id'], self_id)
        if result:
            return web.json_response(True)
        return web.json_response(False)



class AllCompanys(web.View):

    @aiohttp_jinja2.template('company/all_companys.html')
    @get_companys_context
    async def get(self, data):
        session = await get_session(self.request)
        login = session.get('login')
        data.update({'is_socket': False})
        company = comp_model(self.request.app.db)
        # await company.clear_db()

        data['companys'] = await company.get_all_comp()
        data['own_login'] = login
        return data


class Company(web.View):

    @aiohttp_jinja2.template('/company/company.html')
    @get_companys_context
    async def get(self, data, **kw):
        data.update({'is_socket': False})
        company = comp_model(self.request.app.db)
        session = await get_session(self.request)
        self_id = session.get('user')
        login = session.get('login')

        company_id = self.request.rel_url.query.get('id')
        data['company'] = await company.get_company(company_id)

        access = next((x for x in data['company']['users'] if x == self_id), None)
        data['is_member'] = bool(access)
        data['is_admin'] = self_id == data['company']['admin_id']
        data['own_login'] = login

        return data

    async def post(self, **kw):
        data = await self.request.json()
        session = await get_session(self.request)
        self_id = session.get('user')
        company = comp_model(self.request.app.db)
        user = User(self.request.app.db, {})

        comp = await company.get_company(data['company_id'])
        if comp['private'] and comp['password'] != data['password']:
            return web.json_response({'error': 'Неправильный пароль'})
        result = await company.add_user_to_comp(data['company_id'], self_id)
        if result:
            return web.json_response(True)

    async def delete(self, **kw):
        company = comp_model(self.request.app.db)

        data = await self.request.json()
        session = await get_session(self.request)
        self_id = session.get('user')
        if self_id == (await company.get_company(data['company_id']))['admin_id']:
            return web.json_response(True)
        return web.json_response({'error': 'Недостаточно прав.'})
    

async def check_access_to_company(request):
    data = await request.json()
    session = await get_session(request)
    self_id = session.get('user')
    company = comp_model(request.app.db)
    comp = await company.get_company(data['id'])
    access = next((x for x in comp['users'] if x[1] == self_id), None)
    if not access:
        return web.json_response(False)
    return web.json_response(True)