import collections
import aiohttp_jinja2
import json
from aiohttp_session import get_session
from aiohttp import web, WSMsgType
from auth.models import User
from chat.models import Message, UnreadMessage
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


async def main_redirect(request):
    location = request.app.router['main'].url_for()
    raise web.HTTPFound(location=location)


class ChatList(web.View):
    @aiohttp_jinja2.template('chat/index.html')
    async def get(self):
        to_user_login = 'main'
        message = Message(self.request.app.db)
        user = User(self.request.app.db, {})

        session = await get_session(self.request)
        self_id = session.get('user')
        to_user = self.request.rel_url.query.get('id')
        if to_user is not None and to_user != '':
            to_user_login = await user.get_login(to_user)
        users = await user.get_all_users()
        online_id = [x[0] for x in self.request.app['online'].values()]

        if to_user is None or not check_chat([self_id, to_user]):
            chat_name = 'main'
            to_user = None
        else:
            chat_name = create_chat_name(self_id, to_user)
        
        unread = UnreadMessage(self.request.app.db)
        await unread.delete(user_id=self_id, chat_name=chat_name)
        r_unread = await unread.get_messages_recieved(self_id)
        count_r_unr = collections.Counter()
        for mes in r_unread:
            count_r_unr[mes['from_user']] += 1
        s_unread = [x['msg_id'] for x in await unread.get_messages_sent(self_id)]

        messages = await message.get_messages(chat_name)
        # await unread.clear_db()
        # await message.clear_db()
        context = {
            'messages': messages,
            'users': users,
            'online': online_id,
            'chat_name': chat_name,
            'to_user': to_user,
            'unread_mess': s_unread,
            'unread_counter': count_r_unr,
            'login': to_user_login,
        }
        # print(context)
        return context

async def update_unread(request):
    print(request)
    print(dir(request))
    print(request.POST)
    return True


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
            await _ws[1].send_json({'user': login, 'type': 'joined', 'chat_name': chat_name})

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)
                if msg.data == 'close':
                    await ws.close()

                elif data.get('update'):
                    await unread.delete(user_id=self_id, chat_name=chat_name)
                    for _ws in self.request.app['websockets'][chat_name]:
                        await _ws.send_json({'user': login, 'type': 'joined', 'chat_name': chat_name})
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
                    for _ws in self.request.app['websockets'][chat_name]:
                        await _ws.send_json({'user': login, 'msg': data['msg'], 'type': 'msg'})

                    if data['to_user'] != '' and \
                            data['to_user'] is not None and \
                            data['to_user'] in self.request.app['online']:
                        await self.request.app['online'][data['to_user']][1].send_json({
                            'user': login,
                            'msg': data['msg'],
                            'type': 'unread'
                        })
            elif msg.type == WSMsgType.ERROR:
                log.debug('ws connection closed with exception %s' % ws.exception())

        self.request.app['websockets'][chat_name].remove(ws)
        del self.request.app['online'][session.get('user')]
        for _ws in self.request.app['websockets'][chat_name]:
            await _ws.send_json({'user': login, 'type': 'left'})
        log.debug('websocket connection closed')

        return ws
