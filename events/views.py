import json
import collections
import os
import aiohttp_jinja2
from datetime import datetime
from bson.objectid import ObjectId
from aiohttp import web
from aiohttp_session import get_session

from auth.models import User
from events.models import Event as event_model
from events.models import Photo as photo_model
from company.models import Company
from utils import get_context, get_companys_context



class Event(web.View):

    @aiohttp_jinja2.template('events/event.html')
    @get_companys_context
    async def get(self, data):
        event = event_model(self.request.app.db)
        data.update({'is_socket': False})
        session = await get_session(self.request)
        login = session.get('login')

        company_id = self.request.rel_url.query.get('id')
        data.update({'company_id': company_id, 'own_login': login})
        return data

    async def post(self, **kw):
        event = event_model(self.request.app.db)

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
        event = event_model(self.request.app.db)
        if (await event.get_event(data['event_id']))['admin_id'] == self_id:
            result = await event.delete(data['event_id'])
            return web.json_response(True)
        return web.json_response({'error': 'Недостаточно прав'})


class CompEventList(web.View):

    @aiohttp_jinja2.template('events/comp_event_list.html')
    @get_companys_context
    async def get(self, data):
        event = event_model(self.request.app.db)
        company_id = self.request.rel_url.query.get('id')
        session = await get_session(self.request)
        login = session.get('login')

        events = await event.get_events_by_comp(company_id)
        return {'company_id': company_id, 'events': events, 'own_login': login}


class CompEvent(web.View):

    @aiohttp_jinja2.template('events/comp_event.html')
    @get_companys_context
    async def get(self, data):
        company = Company(self.request.app.db)
        event = event_model(self.request.app.db)
        event_id = self.request.rel_url.query.get('id')
        session = await get_session(self.request)
        login = session.get('login')
        self_id = session.get('user')

        event = await event.get_event(event_id)
        comp = await company.get_company(event['company_id'])
        context = {
            'access': self_id in comp['users'],
            'event': event,
            'own_login': login
        }
        return context

class Photo(web.View):

    async def post(self):
        data = await self.request.post()
        if data['photo'] == b'':
            return web.HTTPFound('/comp_event')

        event = event_model(self.request.app.db)
        e = await event.get_event(data['event_id'])

        photo = photo_model(self.request.app.db)
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
