import collections
import aiohttp_jinja2
import json
from typing import List
from aiohttp_session import get_session
from aiohttp import web, WSMsgType

from auth.models import User
from company.models import Company
from chat.models import Message, UnreadMessage
from chat.utils import check_chat, create_chat_name
from settings import log
from utils import get_context


async def main_redirect(request):
    location = request.app.router['account'].url_for()
    raise web.HTTPFound(location=location)


class ChatList(web.View):
    @aiohttp_jinja2.template('chat/index.html')
    # @get_context
    async def get(self, **kw):
        message = Message(self.request.app.db)
        unread = UnreadMessage(self.request.app.db)
        company = Company(self.request.app.db)
        user = User(self.request.app.db, {})
        # to_user_login = 'main'
        session = await get_session(self.request)
        self_id = session.get('user')
        login = session.get('login')

        company_id = self.request.rel_url.query.get('company_id')

        comp = await company.get_company(company_id)
        users = await user.get_logins(comp['users'])

        messages = await message.get_messages_by_company(company_id)
        un_mess = await unread.check_unread(company_id)
        unread_counter = None
        if un_mess is not None:
            unread_counter = un_mess['count']
            for mess in messages:
                if mess['_id'] > un_mess['msg_id']:
                    mess['unread'] = True
                mess['from_user'] = users[mess['from_user']]
        users = [{'login': y, '_id': x} for x, y in users.items()]
        # if to_user is not None and to_user != '':
        #     users_logins = await data['user'].get_login(to_user)

        # if to_user is None or not check_chat([self_id, to_user]):
        #     chat_name = 'main'
        #     to_user = None
        # else:
        #     chat_name = create_chat_name(self_id, to_user)

        # await data['unread'].delete(user_id=self_id, chat_name=chat_name)
        # s_unread = [x['msg_id'] for x in await data['unread'].get_messages_sent(self_id)]

        # message = Message(self.request.app.db)
        # messages = await message.get_messages(chat_name)
        # await data['unread'].clear_db()
        # await data['user'].clear_db()
        # await message.clear_db()
        context = {
            'self_id': self_id,
            'own_login': login,
            'messages': messages,
            'users': users,
            # 'online': '#'.join([x[0] for x in self.request.app['online'].values()]),
            # 'chat_name': chat_name,
            # 'to_user': to_user,
            # 'unread_mess': s_unread,
            'company_id': company_id,
            'unread_counter': unread_counter,
            # 'to_user_login': to_user_login,
            'is_socket': True,
        }
        return context


async def update_unread(request):
    print(request)
    data = await request.json()
    login, to_user = data['login'], data['to_user']
    self_id, chat_name = data['self_id'], data['chat_name']
    unread = UnreadMessage(request.app.db)
    await unread.delete(user_id=self_id, chat_name=chat_name)
    for _ws in request.app['websockets'][chat_name]:
        await _ws.send_json({
            'user_id': self_id,
            'user': login,
            'type': 'read',
            'chat_name': chat_name
        })
    is_online = request.app['online'].get(to_user)
    return web.json_response(bool(is_online))


class CompanyWebSocket(web.View):
    async def get(self):
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)

        session = await get_session(self.request)
        self_id = session.get('user')
        login = session.get('login')
        company_id = self.request.rel_url.query.get('company_id')
        user = User(self.request.app.db, {})
        unread = UnreadMessage(self.request.app.db)
        message = Message(self.request.app.db)
        company = Company(self.request.app.db)
        my_companys = await company.get_company_by_user(self_id)
        # удаляем непрочитанные сообщения при входе в чат
        # await unread.delete(user_id=self_id, chat_name=chat_name)

        for c in my_companys:
            self.request.app['websockets'][str(c['_id'])].append(ws)
        # self.request.app['websockets'][company_id].append(ws)
        self.request.app['online'][session.get('user')] = (login, ws)
        for _ws in self.request.app['online'].values():
            await _ws[1].send_json({
                'user_id': self_id,
                'type': 'joined'
            })

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)
                if msg.data == 'close':
                    await ws.close()

                else:
                    result = await message.save(
                        from_user=self_id,
                        msg=data['msg'],
                        company_id=data['company_id'],
                    )
                    if not await unread.check_unread(data['company_id']):
                        r = await unread.save(
                            from_user=self_id,
                            to_company=data['company_id'],
                            msg_id=result,
                        )
                    else:
                        await unread.add_unread(data['company_id'])

                    mess = {
                        'from': login,
                        'msg': data['msg'],
                        'type': 'msg',
                        'from_id': self_id,
                        'company_id': data['company_id'],
                    }
                    for company_ws in self.request.app['websockets'][company_id]:
                        await company_ws.send_json(mess)

            elif msg.type == WSMsgType.ERROR:
                log.debug('ws connection closed with exception %s' % ws.exception())

        try:
            self.request.app['websockets'][company_id].remove(ws)
        except:
            pass
        del self.request.app['online'][session.get('user')]
        for _ws in self.request.app['websockets'][company_id]:
            await _ws.send_json({'user': login, 'type': 'left'})

        return ws
