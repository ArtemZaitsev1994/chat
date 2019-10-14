import collections
import aiohttp_jinja2
import json
from typing import List
from aiohttp_session import get_session
from aiohttp import web, WSMsgType

from auth.models import User
from chat.models import Message, UnreadMessage
from chat.utils import check_chat, create_chat_name
from settings import log
from utils import get_context


async def main_redirect(request):
    location = request.app.router['main'].url_for()
    raise web.HTTPFound(location=location)


class ChatList(web.View):
    @aiohttp_jinja2.template('chat/index.html')
    @get_context
    async def get(self, data, **kw):
        to_user_login = 'main'
        self_id = data['self_id']

        to_user = self.request.rel_url.query.get('id')
        if to_user is not None and to_user != '':
            to_user_login = await data['user'].get_login(to_user)

        if to_user is None or not check_chat([self_id, to_user]):
            chat_name = 'main'
            to_user = None
        else:
            chat_name = create_chat_name(self_id, to_user)

        await data['unread'].delete(user_id=self_id, chat_name=chat_name)
        s_unread = [x['msg_id'] for x in await data['unread'].get_messages_sent(self_id)]

        message = Message(self.request.app.db)
        messages = await message.get_messages(chat_name)
        # await data['unread'].clear_db()
        # await data['user'].clear_db()
        # await message.clear_db()
        context = {
            'self_id': self_id,
            'own_login': data['login'],
            'messages': messages,
            'users': data['users'],
            'online': data['online_id'],
            'chat_name': chat_name,
            'to_user': to_user,
            'unread_mess': s_unread,
            'unread_counter': data['unread_counter'],
            'to_user_login': to_user_login,
            'is_socket': True,
        }
        return context


async def update_unread(request):
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


class WebSocket(web.View):
    async def get(self):
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)

        session = await get_session(self.request)
        self_id = session.get('user')
        user = User(self.request.app.db, {'id': self_id})
        login = await user.get_login(self_id)
        chat_name = self.request.rel_url.query.get('chat_name')

        unread = UnreadMessage(self.request.app.db)
        message = Message(self.request.app.db)
        # удаляем непрочитанные сообщения при входе в чат
        # await unread.delete(user_id=self_id, chat_name=chat_name)

        self.request.app['websockets'][chat_name].append(ws)
        self.request.app['online'][session.get('user')] = (login, ws)
        for _ws in self.request.app['online'].values():
            await _ws[1].send_json({
                'user_id': self_id,
                'user': login,
                'type': 'joined',
                'chat_name': chat_name
            })

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)
                if msg.data == 'close':
                    await ws.close()

                else:
                    result = await message.save(
                        from_user=login,
                        to_user=data['to_user'],
                        msg=data['msg'],
                        chat_name=data['chat_name'],
                    )
                    r = await unread.save(
                        from_user=self_id,
                        to_user=data['to_user'],
                        msg_id=result,
                        chat_name=data['chat_name']
                    )

                    mess = {
                        'from': login,
                        'to_user': data['to_user'],
                        'msg': data['msg'],
                        'chat_name': data['chat_name'],
                        'to_user_login': data['to_user_login'],
                        'type': 'msg',
                        'from_id': self_id,
                    }
                    try:
                        await self.request.app['online'][data['to_user']][1].send_json(mess)
                    except KeyError:
                            # на случай групповых чатов
                        for _ws in self.request.app['websockets'][chat_name]:
                            await _ws.send_json(mess)

            elif msg.type == WSMsgType.ERROR:
                log.debug('ws connection closed with exception %s' % ws.exception())

        self.request.app['websockets'][chat_name].remove(ws)
        del self.request.app['online'][session.get('user')]
        for _ws in self.request.app['websockets'][chat_name]:
            await _ws.send_json({'user': login, 'type': 'left'})

        return ws
