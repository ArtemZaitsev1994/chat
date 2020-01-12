import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session

from utils import send_notification


class MyCompany(web.View):

    @aiohttp_jinja2.template('company/my_companys.html')
    async def get(self):
        data = self.request['data']
        session = await get_session(self.request)
        self_id = data['self_id']
        company = self.request.app['models']['company']
        my_companys = await company.get_own_companys(self_id)
        data['my_companys'] = my_companys
        return data

    async def post(self):
        session = await get_session(self.request)
        self_id = session.get('user')

        company = self.request.app['models']['company']
        data = await self.request.json()
        if await company.create_company(data, self_id):
            return web.json_response(True)
        return web.json_response({'error': 'ТусЭ уже есть.'})

    async def delete(self):
        session = await get_session(self.request)
        self_id = session.get('user')

        data = await self.request.json()
        company = self.request.app['models']['company']

        result = await company.delete_user_from_comp(data['company_id'], self_id)
        return web.json_response(bool(result))



class AllCompanys(web.View):
    @aiohttp_jinja2.template('company/all_companys.html')
    async def get(self):
        data = self.request['data']
        session = await get_session(self.request)
        self_id = data['self_id']

        company = self.request.app['models']['company']
        event = self.request.app['models']['event']

        companys = await company.get_companys_by_user(self_id)

        data['companys'] = {x['_id']: x['name'] for x in await company.get_all()}
        data['events'] = await event.get_events_by_companys(companys)
        print(data)
        return data



class Company(web.View):
    CHANNEL_NAME = 'company'

    @aiohttp_jinja2.template('/company/company.html')
    async def get(self):
        data = self.request['data']
        company = self.request.app['models']['company']
        unread = self.request.app['models']['unread']
        user = self.request.app['models']['user']
        invite = self.request.app['models']['invite']

        session = await get_session(self.request)
        self_id = data['self_id']

        company_id = self.request.rel_url.query.get('id')
        data['company'] = await company.get_company(company_id)
        data['company_id'] = company_id

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

    async def post(self):
        data = await self.request.json()
        session = await get_session(self.request)
        self_id = session.get('user')
        self_login = session.get('login')
        company = self.request.app['models']['company']

        comp = await company.get_company(data['company_id'])
        if comp['private'] and comp['password'] != data['password']:
            return web.json_response({'error': 'Неправильный пароль'})
        result = await company.add_user_to_comp(data['company_id'], self_id)
        if result:  
            data = {}
            data['company_id'] = str(comp['_id'])
            data['company_name'] = comp['name']
            data['self_login'] = self_login
            data['payload'] = f'{self_login} вступил в {comp["name"]}.'

            await send_notification(self.request.app, data, self.CHANNEL_NAME)
        return web.json_response(bool(result))

    async def delete(self):
        session = await get_session(self.request)
        self_id = session.get('user')
        company = self.request.app['models']['company']

        data = await self.request.json()
        if self_id == (await company.get_company(data['company_id']))['admin_id']:
            return web.json_response(True)
        return web.json_response({'error': 'Недостаточно прав.'})


async def check_access_to_company(request):
    """Проверка пользователя на доступ к материалам компании"""
    data = await request.json()
    session = await get_session(request)
    self_id = session.get('user')
    company = request.app['models']['company']
    comp = await company.get_company(data['id'])
    access = next((x for x in comp['users'] if x[1] == self_id), None)
    return web.json_response(bool(access))


class CompanyDetails(web.View):
    @aiohttp_jinja2.template('/company/company_details.html')
    async def get(self):
        data = self.request['data']
        company = self.request.app['models']['company']
        user = self.request.app['models']['user']
        session = await get_session(self.request)
        self_id = data['self_id']

        company_id = self.request.rel_url.query.get('company_id')
        comp = await company.get_company(company_id)
        if self_id in comp['users']:
            comp['users'].remove(self_id)
        comp['users'] = await user.get_users(comp['users'])

        data['company'] = comp
        data['access'] = await company.check_access(company_id, self_id)

        return data

    async def post(self):
        """
        работа с юзерами
        """
        company = self.request.app['models']['company']
        session = await get_session(self.request)
        self_id = session.get('user')

        data = await self.request.json()
        if not await company.check_access(data['company_id'], self_id):
            return web.json_response()
        if data['delete']:
            await company.delete_user_from_comp(data['company_id'], data['user_id'])
        else:
            await company.add_user_to_comp(data['company_id'], data['user_id'])
        return web.json_response(True)

