import json
import collections
import os
import aiohttp_jinja2

from datetime import datetime
from bson.objectid import ObjectId
from aiohttp import web
from aiohttp_session import get_session

from utils import get_context, get_companys_context



class Event(web.View):

    @aiohttp_jinja2.template('events/event.html')
    async def get(self):
        event = self.request.app['models']['event']
        data = {'is_socket': False}
        session = await get_session(self.request)
        login = session.get('login')

        company_id = self.request.rel_url.query.get('id')
        data.update({'company_id': company_id, 'own_login': login})
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
        event = self.request.app['models']['event']
        company_id = self.request.rel_url.query.get('id')
        session = await get_session(self.request)
        login = session.get('login')

        events = await event.get_events_by_comp(company_id)
        print(events)
        return {'company_id': company_id, 'events': events, 'own_login': login}


class CompEvent(web.View):

    @aiohttp_jinja2.template('events/comp_event.html')
    async def get(self):
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
            'company_name': comp['name'] 
        }
        return context

class Photo(web.View):

    async def post(self):
        data = await self.request.post()
        if data['photo'] == b'':
            return web.HTTPFound('/comp_event')

        rel_url = str(self.request.rel_url)

        photo = self.request.app['models']['photo']
        if rel_url == '/user_avatar':
            user = self.request.app['models']['user']
            user.id = data['user_id']
            u = await user.check_user()
            filename = str(await photo.create_avatar(data['user_id']))
            direction = os.path.join(self.request.app['avatar_dir'], f'{data["user_id"]}/')
        elif rel_url == r'/photo':
            event = self.request.app['models']['event']
            e = await event.get_event(data['event_id'])
            filename = str(await photo.create_photo(data['event_id']))
            direction = os.path.join(self.request.app['photo_dir'], f'{data["event_id"]}/')
            
        filename = f'{filename}.{data["photo"].filename.split(".")[-1]}'
        input_file = data['photo'].file

        if not os.path.exists(direction):
            os.makedirs(direction)

        with open(os.path.join(direction, filename), 'wb') as f:
            f.write(input_file.read())

        if rel_url == '/user_avatar':
            await user.set_avatar(data['user_id'], filename)
        elif rel_url == r'/photo':
            await event.add_photo(data['event_id'], filename)
            if e['avatar'] == '':
                await event.add_avatar(data['event_id'], filename)

        return web.Response()
