import aiohttp_jinja2
import collections
from aiohttp import web
from aiohttp_session import get_session

from auth.models import User
from chat.models import UnreadMessage


@aiohttp_jinja2.template('about/about.html')
async def about_main(request):
    user = User(request.app.db, {})

    session = await get_session(request)
    self_id = session.get('user')
    login = await user.get_login(self_id)
    users = await user.get_all_users()

    unread = UnreadMessage(request.app.db)
    r_unread = await unread.get_messages_recieved(self_id)
    unread_counter = collections.Counter()
    for mes in r_unread:
        unread_counter[mes['from_user']] += 1

    photo_path = 'photo/main.gif'

    context = {
        'users': users,
        'own_login': login,
        'photo_path': photo_path,
        'unread_counter': unread_counter, 
    }
    return context