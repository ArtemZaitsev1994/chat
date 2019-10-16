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
        data.update({'is_socket': False})
        return data

    async def post(self, **kw):
        user = User(self.request.app.db, {})
        company = comp_model(self.request.app.db)

        data = await self.request.json()
        session = await get_session(self.request)
        self_id = session.get('user')
        login = await user.get_login(self_id)
        if await company.create_company(data, self_id, login):
            return web.json_response(True)
        return web.json_response({'error': 'ТусЭ уже есть.'})


class AllCompanys(web.View):

    @aiohttp_jinja2.template('company/all_companys.html')
    @get_companys_context
    async def get(self, data):
        data.update({'is_socket': False})
        company = comp_model(self.request.app.db)

        data['companys'] = await company.get_all_comp()
        return data


class Company(web.View):

    @aiohttp_jinja2.template('/company/company.html')
    @get_companys_context
    async def get(self, data, **kw):
        data.update({'is_socket': False})
        company = comp_model(self.request.app.db)
        session = await get_session(self.request)
        self_id = session.get('user')

        company_id = self.request.rel_url.query.get('id')
        data['company'] = await company.get_company(company_id)

        access = next((x for x in data['company']['users'] if x[1] == self_id), None)
        data['is_member'] = True if access else False

        return data

    async def post(self, **kw):
        data = await self.request.json()
        session = await get_session(self.request)
        self_id = session.get('user')
        company = comp_model(self.request.app.db)
        user = User(self.request.app.db, {})

        login = await user.get_login(self_id)
        comp = await company.get_company(data['company_id'])
        print(comp)
        if comp['private'] and comp['password'] != data['password']:
            return web.json_response({'error': 'Неправильный пароль'})
        result = await company.add_user_to_comp(data['company_id'], self_id, login)
        if result:
            return web.json_response(True)
    
    async def delete(self, **kw):
        data = await self.request.json()
        session = await get_session(self.request)
        self_id = session.get('user')
        company = comp_model(self.request.app.db)
        user = User(self.request.app.db, {})

        login = await user.get_login(self_id)
        result = await company.delete_user_from_comp(data['company_id'], self_id, login)
        if result:
            return web.json_response(True)
        return web.json_response(False)
    

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