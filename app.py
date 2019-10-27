import asyncio
import aiohttp_jinja2
import jinja2
import hashlib
import collections
import os
from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttp import web

from routes import routes
from middlewares import authorize
from motor import motor_asyncio as ma
from settings import *


basedir = os.path.dirname(os.path.realpath(__file__))
photo_dir = os.path.join(basedir, 'static/photo/')

async def on_shutdown(app):
    for ws in app['websockets']:
        await ws.close(code=1001, mesage='Server shutdown')

middle = [
    session_middleware(EncryptedCookieStorage(hashlib.sha256(bytes(SECRET_KEY, 'utf-8')).digest())),
    authorize
]

app = web.Application(middlewares=middle)

aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))

for route in routes:
    app.router.add_route(*route[:3], name=route[3])
app['static_root_url'] = '/static'
app.router.add_static('/static', 'static', name='static')

app.client = ma.AsyncIOMotorClient(MONGO_HOST)
app.db = app.client[MONGO_DB_NAME]

app.on_cleanup.append(on_shutdown)
app['websockets'] = collections.defaultdict(list)
app['online'] = {}
app['photo_dir'] = photo_dir

web.run_app(app)
