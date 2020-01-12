from aiohttp import web
from aiohttp.web import middleware
from aiohttp_session import get_session


@middleware
async def authorize(request, handler):
    def check_path(path):
        """
        Проверка разрешен ли путь
        """
        result = False
        for r in ['/login', '/static/', '/signin', '/signout', '/_debugtoolbat/']:
            if path.startswith(r):
                result = True
        return result

    session = await get_session(request)
    if session.get('user'):
        if request.method == "GET":
            request['data'] = await get_common_data(session, request)
        return await handler(request)
    else:
        if not check_path(request.path):
            url = request.app.router['login'].url_for()
            raise web.HTTPFound(url)
        return await handler(request)


async def get_common_data(session, request):
    self_id = session.get('user')
    last_notif = await request.app['models']['notif'].get_last_notification(self_id)

    data = {
        'own_login': session.get('login'),
        'self_id': self_id,
        'last_notif': last_notif,
    }
    return data

