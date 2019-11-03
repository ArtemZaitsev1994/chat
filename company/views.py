import json
import collections
import aiohttp_jinja2
from time import time
from bson.objectid import ObjectId
from aiohttp import web
from aiohttp_session import get_session

from utils import get_context, get_companys_context
from auth.utils import redirect, set_session, convert_json


class MyCompany(web.View):

    @aiohttp_jinja2.template('company/my_companys.html')
    async def get(self):
        session = await get_session(self.request)
        login = session.get('login')
        data = {'is_socket': False, 'own_login': login}
        return data

    async def post(self, **kw):
        company = self.request.app['models']['company']

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
        company = self.request.app['models']['company']
        user = self.request.app['models']['user']

        result = await company.delete_user_from_comp(data['company_id'], self_id)
        if result:
            return web.json_response(True)
        return web.json_response(False)



class AllCompanys(web.View):

    @aiohttp_jinja2.template('company/all_companys.html')
    async def get(self):
        session = await get_session(self.request)
        login = session.get('login')
        data = {'is_socket': False}
        company = self.request.app['models']['company']
        # await company.clear_db()

        data['companys'] = await company.get_all_comp()
        data['own_login'] = login
        return data


class Company(web.View):

    @aiohttp_jinja2.template('/company/company.html')
    async def get(self, **kw):
        data = {'is_socket': False}
        company = self.request.app['models']['company']
        unread = self.request.app['models']['unread']
        user = self.request.app['models']['user']
        invite = self.request.app['models']['invite']
        session = await get_session(self.request)
        self_id = session.get('user')
        login = session.get('login')

        company_id = self.request.rel_url.query.get('id')
        data['company'] = await company.get_company(company_id)

        access = next((x for x in data['company']['users'] if x == self_id), None)
        data['is_member'] = bool(access)
        if data['is_member']:
            data['is_admin'] = self_id == data['company']['admin_id']
            data['count_inv'] = await invite.get_invites_number(company_id)
        else:
            data['users'] = await user.get_logins(data['company']['users'])
            inv = await invite.get_invite_to_company(self_id, company_id)
            data['action_btn'] = 'Отправить запрос на вступление'
            if inv:
                data['action'] = f'Запрос отправлен. Статус: {inv["status"]}'
                data['action_btn'] = 'Отменить запрос'
                data['sent_invite'] = True
                data['inv_status'] = inv['status'] 

        unr_mess = await unread.check_unread(company_id, self_id)
        data['unread'] = unr_mess['count'] if unr_mess else 0

        return data

    async def post(self, **kw):
        data = await self.request.json()
        session = await get_session(self.request)
        self_id = session.get('user')
        company = self.request.app['models']['company']
        user = self.request.app['models']['user']

        comp = await company.get_company(data['company_id'])
        if comp['private'] and comp['password'] != data['password']:
            return web.json_response({'error': 'Неправильный пароль'})
        result = await company.add_user_to_comp(data['company_id'], self_id)
        if result:
            return web.json_response(True)

    async def delete(self, **kw):
        company = self.request.app['models']['company']

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
    company = request.app['models']['company']
    comp = await company.get_company(data['id'])
    access = next((x for x in comp['users'] if x[1] == self_id), None)
    if not access:
        return web.json_response(False)
    return web.json_response(True)
