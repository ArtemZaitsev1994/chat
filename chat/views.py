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
        """
        Получение информации о чате внутри одной тусовки
        """
        message = Message(self.request.app.db)
        unread = UnreadMessage(self.request.app.db)
        company = Company(self.request.app.db)
        user = User(self.request.app.db, {})
        session = await get_session(self.request)
        self_id = session.get('user')
        login = session.get('login')

        company_id = self.request.rel_url.query.get('company_id')

        comp = await company.get_company(company_id)
        users = await user.get_logins(comp['users'])

        messages = await message.get_messages_by_company(company_id)
        last_mess_author = messages[-1]['from_user']
        unr_mess = await unread.check_unread(company_id, self_id)
        unread_counter = collections.defaultdict(int)
        if unr_mess is not None:
            unread_counter['main_chat'] = unr_mess['count']
        for mess in messages:
            if unr_mess is not None and mess['_id'] >= unr_mess['msg_id']:
                mess['unread'] = True
            mess['from_user'] = users[mess['from_user']]
        unread_counter.update(await unread.count_unread(self_id))
        await unread.delete_by_company(company_id, self_id)

        users = [{'login': y, '_id': x} for x, y in users.items()]
        online = [str(x[0]) for x in self.request.app['online'].values()]
        online.append(self_id)
        context = {
            'self_id': self_id,
            'own_login': login,
            'messages': messages,
            'users': users,
            'online': '#'.join(online),
            'company_id': company_id,
            'unread_counter': unread_counter,
            'is_socket': True,
            'last_mess_author': last_mess_author,
        }
        return context


async def update_unread_company(request):
    """
    Прочитываем сообщения внутри одной комнаты
    приходит ajax-запрос
    """
    data = await request.json()
    session = await get_session(request)
    self_id = session.get('user')
    login = session.get('login')
    unread = UnreadMessage(request.app.db)
    await unread.delete_by_company(data['company_id'], self_id)
    for _ws in request.app['websockets'][data['company_id']]:
        await _ws.send_json({
            'user_id': self_id,
            'user': login,
            'type': 'read',
            'company_id': data['company_id']
        })
    return web.json_response(True)

async def update_unread(request):
    """
    Прочитываем сообщения внутри одной комнаты
    приходит ajax-запрос
    """
    data = await request.json()
    session = await get_session(request)
    self_id = session.get('user')
    login = session.get('login')
    unread = UnreadMessage(request.app.db)
    await unread.delete(self_id, data['from_user'])
    try:
        await request.app['online'][data['from_user']][1].send_json({'type': 'read', 'user_id': self_id})
    except KeyError:
        is_online = False
    else:
        is_online = True
    return web.json_response(is_online)


class UserChatCompany(web.View):
    async def post(self):
        """
        Комната чата внутри одной компании - общий чат
        """
        message = Message(self.request.app.db)
        unread = UnreadMessage(self.request.app.db)
        user = User(self.request.app.db, {})
        session = await get_session(self.request)
        self_id = session.get('user')
        company_id = (await self.request.json())['company_id']
        company = Company(self.request.app.db)
        comp = await company.get_company(company_id)
        users = await user.get_logins(comp['users'])
        messages = await message.get_messages_by_company(company_id)
        last_mess_author = messages[-1]['from_user']
        unr_mess = await unread.check_unread(company_id, self_id)
        if unr_mess is not None and self_id != unr_mess['from_user']:
            await unread.delete_by_company(company_id, self_id)
        for mess in messages:
            if unr_mess is not None and self_id == unr_mess['from_user'] and mess['_id'] >= unr_mess['msg_id']:
                mess['unread'] = True
            mess['_id'] = str(mess['_id'])
            mess['time'], _ = str(mess["time"].time()).split('.')
            mess['from_user'] = users[mess['from_user']]
        return web.json_response({'messages': messages, 'last_mess_author': last_mess_author})

class UserChat(web.View):
    async def post(self):
        """
        Комната чата с каким-либо другим пользователем, tet-a-tet
        """
        message = Message(self.request.app.db)
        unread = UnreadMessage(self.request.app.db)
        user = User(self.request.app.db, {})
        session = await get_session(self.request)
        self_id = session.get('user')
        user_id = (await self.request.json())['user_id']
        users = await user.get_logins([self_id, user_id])
        chat_name = create_chat_name(self_id, user_id)
        unr_mess = await unread.get_unread_user_chat(self_id, user_id)
        if not unr_mess:
            await unread.delete(self_id, user_id)
        messages = await message.get_messages(chat_name)
        last_mess_author = messages[-1]['from_user']
        for mess in messages:
            if unr_mess is not None and self_id == unr_mess['from_user'] and mess['_id'] > unr_mess['msg_id']:
                mess['unread'] = True
            mess['_id'] = str(mess['_id'])
            mess['time'], _ = str(mess["time"].time()).split('.')
            mess['from_user'] = users[mess['from_user']]
        try:
            await self.request.app['online'][user_id][1].send_json({'type': 'read', 'user_id': self_id})
        except KeyError:
            is_online = False
        else:
            is_online = True
        answer = {
            'messages': messages,
            'chat_name': chat_name,
            'is_online': is_online, 
            'last_mess_author': last_mess_author
        }
        return web.json_response(answer)



class CompanyWebSocket(web.View):
    """
    Класс websocket-а, вся логика интерактивной работы с пользователем
    TODO: всплывающие popup уведомления о ивентах
    """
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

        for c in my_companys:
            self.request.app['websockets'][str(c['_id'])].append(ws)
        # self.request.app['websockets'][company_id].append(ws)
        self.request.app['online'][session.get('user')] = (self_id, ws)
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
                    if data['company_id']:
                        comp = await company.get_company(data['company_id'])

                        result = await message.save_for_company(
                            from_user=self_id,
                            msg=data['msg'],
                            company_id=data['company_id'],
                        )
                        for u in comp['users']:
                            if u == self_id:
                                continue
                            if not await unread.check_unread(data['company_id'], self_id):
                                r = await unread.save_for_company(
                                    from_user=self_id,
                                    to_user=u,
                                    to_company=data['company_id'],
                                    msg_id=result,
                                )
                            else:
                                await unread.add_unread(data['company_id'])
                    else:
                        result = await message.save(
                                chat_name=data['chat_name'],
                                from_user=self_id,
                                msg=data['msg'],
                                to_user=data['to_user']
                            )
                        if not await unread.get_unread_user_chat(self_id, data['to_user']) and self_id != data['to_user']:
                            r = await unread.save(
                                from_user=self_id,
                                to_user=data['to_user'],
                                msg_id=result,
                            )
                        else:
                            await unread.add_unread_user_chat(self_id, data['to_user'])
                    mess = {
                        'from': login,
                        'msg': data['msg'],
                        'type': 'msg',
                        'from_id': self_id,
                        'to_user': data['to_user'],
                        'company_id': data['company_id'],
                        'chat_name': data.get('chat_name')
                    }
                    if data['company_id']:
                        # отправляем сообщения всем юзерам входящим в эту компанию
                        for company_ws in self.request.app['websockets'][company_id]:
                            print(self.request.app['websockets'])
                            await company_ws.send_json(mess)
                            print(2)
                    elif self_id == data['to_user']:
                            # если общаемся с самим собой
                            await self.request.app['online'][self_id][1].send_json(mess)
                    else:
                        # Отправляем сообщение юзеру to_user
                        try:
                            await self.request.app['online'][data['to_user']][1].send_json(mess)
                        except:
                            pass
                        # Отправляем сообщение себе
                        finally:
                            await self.request.app['online'][self_id][1].send_json(mess)

            elif msg.type == WSMsgType.ERROR:
                log.debug('ws connection closed with exception %s' % ws.exception())

        try:
            self.request.app['websockets'][company_id].remove(ws)
        except:
            pass
        del self.request.app['online'][session.get('user')]
        for _ws in self.request.app['websockets'][company_id]:
            await _ws.send_json({'user': login, 'type': 'left'})
            print(self_id)

        return ws

class CommonWebSocket(web.View):
    """
    Класс websocket-а, вся логика интерактивной работы с пользователем
    TODO: всплывающие popup уведомления о ивентах
    """
    async def get(self):
        print(11)
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

        for c in my_companys:
            self.request.app['websockets'][str(c['_id'])].append(ws)
        # self.request.app['websockets'][company_id].append(ws)
        self.request.app['online'][session.get('user')] = (self_id, ws)
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
                    if data['company_id']:
                        comp = await company.get_company(data['company_id'])

                        result = await message.save_for_company(
                            from_user=self_id,
                            msg=data['msg'],
                            company_id=data['company_id'],
                        )
                        for u in comp['users']:
                            if u == self_id:
                                continue
                            if not await unread.check_unread(data['company_id'], self_id):
                                r = await unread.save_for_company(
                                    from_user=self_id,
                                    to_user=u,
                                    to_company=data['company_id'],
                                    msg_id=result,
                                )
                            else:
                                await unread.add_unread(data['company_id'])
                    else:
                        result = await message.save(
                                chat_name=data['chat_name'],
                                from_user=self_id,
                                msg=data['msg'],
                                to_user=data['to_user']
                            )
                        if not await unread.get_unread_user_chat(self_id, data['to_user']) and self_id != data['to_user']:
                            r = await unread.save(
                                from_user=self_id,
                                to_user=data['to_user'],
                                msg_id=result,
                            )
                        else:
                            await unread.add_unread_user_chat(self_id, data['to_user'])
                    mess = {
                        'from': login,
                        'msg': data['msg'],
                        'type': 'msg',
                        'from_id': self_id,
                        'to_user': data['to_user'],
                        'company_id': data['company_id'],
                        'chat_name': data.get('chat_name')
                    }
                    if data['company_id']:
                        # отправляем сообщения всем юзерам входящим в эту компанию
                        for company_ws in self.request.app['websockets'][company_id]:
                            await company_ws.send_json(mess)
                    elif self_id == data['to_user']:
                            # если общаемся с самим собой
                            await self.request.app['online'][self_id][1].send_json(mess)
                    else:
                        # Отправляем сообщение юзеру to_user
                        try:
                            await self.request.app['online'][data['to_user']][1].send_json(mess)
                        except:
                            pass
                        # Отправляем сообщение себе
                        finally:
                            await self.request.app['online'][self_id][1].send_json(mess)

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