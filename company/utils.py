import json
from time import time
from aiohttp import web


def redirect(request, router_name):
    url = request.app.router[router_name].url_for()
    raise web.HTTPFound(url)


def set_session(session, user_id, request):
    session['user'] = str(user_id)
    session['last_visit'] = time()
    redirect(request, 'main')


def convert_json(message):
    return json.dumps({'error': message})
