import json
from time import time

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp_session import Session


def redirect(request: Request, router_name: str):
    url = request.app.router[router_name].url_for()
    raise web.HTTPFound(url)


def set_session(session: Session, user_id: str, login: str, request: Request):
    session['user'] = str(user_id)
    session['login'] = login
    session['last_visit'] = time()
    redirect(request, 'account')


def convert_json(message):
    return json.dumps({'error': message})
