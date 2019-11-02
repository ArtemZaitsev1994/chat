import collections
from aiohttp import web
from aiohttp_session import get_session
from auth.models import User
from chat.models import UnreadMessage
from company.models import Company


def get_context(func):
    async def wrap(self):
        session = await get_session(self.request)

        user = self.request.app['models']['user']
        users = await user.get_all_users()
        self_id = session.get('user')
        login = session.get('login')

        unread = self.request.app['models']['unread']
        r_unread = await unread.get_messages_recieved(self_id)
        unread_counter = collections.Counter()

        online_id = '#'.join([x[0] for x in self.request.app['online'].values()])
        context = {
            'user': user,
            'users': users,
            'session': session,
            'self_id': self_id,
            'login': login,
            'unread': unread,
            'unread_counter': unread_counter,
            'online_id': online_id,
        }
        return await func(self, context)
    return wrap


def get_companys_context(func):
    async def wrap(self):
        session = await get_session(self.request)
        self_id = session.get('user')
        login = session.get('login')

        context = {
            'self_id': self_id,
            'login': login,
        }
        return await func(self, context)
    return wrap
