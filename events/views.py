import os
import json
from typing import Dict, Any

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session
from utils import send_notification


class Event(web.View):
    CHANNEL_NAME = 'events'

    @aiohttp_jinja2.template('events/event.html')
    async def get(self):
        data = self.request.get('data', {})
        company_id = self.request.rel_url.query.get('id')
        data['company_id'] = company_id
        return data

    async def post(self,):
        event = self.request.app['models']['event']
        comp = self.request.app['models']['company']

        data = await self.request.json()
        company = await comp.get_company(data['company_id'])
        session = await get_session(self.request)
        self_id = session.get('user')
        self_login = session.get('login')
        if await event.create_event(data, self_id):
            data = {}
            data['company_id'] = str(company['_id'])
            data['company_name'] = company['name']
            data['type'] = 'new_event'
            data['self_login'] = self_login
            data['payload'] = f'{self_login} создал новый ивент в {company["name"]}.'
            
            await send_notification(self.request.app, data, self.CHANNEL_NAME)
            return web.json_response(True)
        return web.json_response({'error': 'Ивент с таким именем уже есть.'})
    
    async def delete(self):
        data = await self.request.json()
        session = await get_session(self.request)
        self_id = session.get('user')
        event = self.request.app['models']['event']
        if (await event.get_event(data['event_id']))['admin_id'] == self_id:
            return web.json_response(bool(await event.delete(data['event_id'])))
        return web.json_response({'error': 'Недостаточно прав'})


class CompEventList(web.View):

    @aiohttp_jinja2.template('events/comp_event_list.html')
    async def get(self):
        data = self.request.get('data', {})
        event = self.request.app['models']['event']
        company_id = self.request.rel_url.query.get('id')
        data['company_id'] = company_id

        events = await event.get_events_by_comp(company_id)
        data['events'] = events
        return data


class CompEvent(web.View):

    @aiohttp_jinja2.template('events/comp_event.html')
    async def get(self):
        data = self.request.get('data', {})
        company = self.request.app['models']['company']
        event = self.request.app['models']['event']
        event_id = self.request.rel_url.query.get('id')
        self_id = data['self_id']

        event = await event.get_event(event_id)
        comp = await company.get_company(event['company_id'])
        context = {
            'access': self_id in comp['users'],
            'event': event,
            'company_name': comp['name'],
        }

        data.update(context)
        return data


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
