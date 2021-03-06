import json
import os

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session


class Invite(web.View):

    @aiohttp_jinja2.template('invite/invite_list.html')
    async def get(self):
        data = self.request.get('data', {})
        invite = self.request.app['models']['invite']
        user = self.request.app['models']['user']
        company = self.request.app['models']['company']
        company_id = self.request.rel_url.query.get('company_id')
        company_name = (await company.get_company(company_id))['name']

        invites = await invite.get_invites_by_comp(company_id, 'Ожидает')
        for i in invites:
            i['login'] = await user.get_login(i['user_id'])

        data.update({'invites': invites, 'company_id': company_id, 'company_name': company_name})
        return data 

    async def post(self):
        invite = self.request.app['models']['invite']

        data = await self.request.json()
        session = await get_session(self.request)

        self_id = session.get('user')
        if await invite.create_invite(self_id, data):
            return web.json_response(True)
        return web.json_response({'error': 'something went wrong'})

    async def delete(self):
        invite = self.request.app['models']['invite']

        data = await self.request.json()
        session = await get_session(self.request)

        self_id = session.get('user')
        if await invite.delete(self_id, data['company_id']):
            return web.json_response(True)
        return web.json_response({'error': 'something went wrong'})

    async def put(self):
        invite = self.request.app['models']['invite']
        company = self.request.app['models']['company']

        data = await self.request.json()
        if data['type']:
            if await invite.accept_invite(data):
                await company.add_user_to_comp(data['company_id'], data['user_id'])
                return web.json_response(True)
        else:
            if await invite.decline_invite(data):
                return web.json_response(True)
        return web.json_response({'error': 'something went wrong'})


class Event(web.View):

    @aiohttp_jinja2.template('events/event.html')
    async def get(self):
        data = self.request.get('data', {})
        event = self.request.app['models']['event']

        company_id = self.request.rel_url.query.get('id')
        data['company_id'] = company_id
        return data

    async def post(self, **kw):
        event = self.request.app['models']['event']

        data = await self.request.json()
        session = await get_session(self.request)
        self_id = session.get('user')
        if await event.create_event(data, self_id):
            return web.json_response(True)
        return web.json_response({'error': 'Ивент с таким именем уже есть.'})
    
    async def delete(self, **kw):
        data = await self.request.json()
        session = await get_session(self.request)
        self_id = session.get('user')
        event = self.request.app['models']['event']
        if (await event.get_event(data['event_id']))['admin_id'] == self_id:
            result = await event.delete(data['event_id'])
            return web.json_response(True)
        return web.json_response({'error': 'Недостаточно прав'})


class CompEventList(web.View):

    @aiohttp_jinja2.template('events/comp_event_list.html')
    async def get(self):
        data = self.request.get('data', {})
        event = self.request.app['models']['event']
        company_id = self.request.rel_url.query.get('id')

        events = await event.get_events_by_comp(company_id)
        data.update({'company_id': company_id, 'events': events})
        return data


class CompEvent(web.View):

    @aiohttp_jinja2.template('events/comp_event.html')
    async def get(self):
        data = self.request.get('data', {})
        company = self.request.app['models']['company']
        event = self.request.app['models']['event']
        event_id = self.request.rel_url.query.get('id')
        session = await get_session(self.request)
        login = session.get('login')
        self_id = session.get('user')

        event = await event.get_event(event_id)
        comp = await company.get_company(event['company_id'])
        context = {
            'access': self_id in comp['users'],
            'event': event,
            'own_login': login,
            'self_id': self_id
        }
        return context

class Photo(web.View):

    async def post(self):
        data = await self.request.post()
        if data['photo'] == b'':
            return web.HTTPFound('/comp_event')

        event = self.request.app['models']['event']
        e = await event.get_event(data['event_id'])

        photo = self.request.app['models']['photo']
        filename = str(await photo.create_photo(data['event_id']))
        filename = f'{filename}.{data["photo"].filename.split(".")[-1]}'
        input_file = data['photo'].file
        event_dir = os.path.join(self.request.app['photo_dir'], f'{data["event_id"]}/')
        if not os.path.exists(event_dir):
            os.makedirs(event_dir)

        with open(os.path.join(event_dir, filename), 'wb') as f:
            f.write(input_file.read())

        await event.add_photo(data['event_id'], filename)
        if e['avatar'] == '':
            await event.add_avatar(data['event_id'], filename)

        return web.Response()
