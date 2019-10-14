import collections
from aiohttp import web
from aiohttp_session import get_session
from auth.models import User
from chat.models import UnreadMessage


def get_context(func):
    async def wrap(self):
        session = await get_session(self.request)

        user = User(self.request.app.db, {})
        users = await user.get_all_users()
        self_id = session.get('user')
        login = await user.get_login(self_id)

        unread = UnreadMessage(self.request.app.db)
        r_unread = await unread.get_messages_recieved(self_id)
        unread_counter = collections.Counter()
        for mes in r_unread:
            unread_counter[mes['from_user']] += 1

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
