import aiohttp_jinja2
import json
from aiohttp_session import get_session
from aiohttp import web, WSMsgType
from auth.models import User
from chat.models import Message
from settings import log
from typing import List


def check_chat(ids: List[str]) -> bool:
    for i in ids:
        try:
            int(i, 16)
        except ValueError as e:
            return False
        else:
            return True

def create_chat_name(first_user: str, second_user: str) -> str:
    if int(first_user, 16) < int(second_user, 16):
        return f'{first_user}_{second_user}'
    elif int(first_user, 16) > int(second_user, 16):
        return f'{second_user}_{first_user}'
    else:
        return first_user


class ChatList(web.View):
    @aiohttp_jinja2.template('chat/index.html')
    async def get(self):
        message = Message(self.request.app.db)
        user = User(self.request.app.db, {})
        session = await get_session(self.request)
        current_user = session.get('user')
        another_login = self.request.rel_url.query.get('id')
        users = await user.get_all_users()
        online = list(self.request.app['online'])
        if another_login is None or not check_chat([current_user, another_login]):
            messages = await message.get_messages('main')
            return {'messages': messages, 'users': users, 'online': online, 'chat_name': 'main'}
        chat_name = create_chat_name(current_user, another_login)
        messages = await message.get_messages(chat_name)
        return {
            'messages': messages,
            'users': users,
            'online': online,
            'chat_name': chat_name,
            'another_login': another_login
        }


class WebSocket(web.View):
    async def get(self):
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)

        session = await get_session(self.request)
        user = User(self.request.app.db, {'id': session.get('user')})
        login = await user.get_login()
        chat_name = self.request.rel_url.query.get('chat_name')

        self.request.app['websockets'][chat_name].append(ws)
        self.request.app['online'][login] = login
        for _ws in self.request.app['websockets'][chat_name]:
            await _ws.send_json({'user': login, 'type': 'joined'})

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
                else:
                    data = json.loads(msg.data)
                    message = Message(self.request.app.db)
                    result = await message.save(user=login, msg=data['msg'], chat_name=data['chat_name'])
                    log.debug(result)
                    for _ws in self.request.app['websockets'][chat_name]:
                        await _ws.send_json({'user': login, 'msg': data['msg'], 'type': 'msg'})
            elif msg.type == WSMsgType.ERROR:
                log.debug('ws connection closed with exception %s' % ws.exception())

        self.request.app['websockets'][chat_name].remove(ws)
        del self.request.app['online'][login]
        for _ws in self.request.app['websockets'][chat_name]:
            await _ws.send_json({'user': login, 'type': 'left'})
        log.debug('websocket connection closed')

        return ws
