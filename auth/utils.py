import json
from time import time

from aiohttp import web


def redirect(request: TODO, router_name: str):
    url = request.app.router[router_name].url_for()
    raise web.HTTPFound(url)


def set_session(session: TODO, user_id: str, login: str, request: TODO):
    session['user'] = str(user_id)
    session['login'] = login
    session['last_visit'] = time()
    redirect(request, 'account')


def convert_json(message):
    return json.dumps({'error': message})
