import hashlib
import collections
import os
import asyncio
import aiohttp_jinja2
import aiohttp_session
import jinja2
from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttp_session.redis_storage import RedisStorage
from aiohttp import web
from motor import motor_asyncio as ma

from middlewares import authorize
from routes import routes
from utils import create_models, create_redis, close_redis, make_redis_pool
from settings import SECRET_KEY, MONGO_DB_NAME, MONGO_HOST, PHOTO_DIR, AVATAR_DIR


loop = asyncio.get_event_loop()
redis_pool = loop.run_until_complete(make_redis_pool())
storage = RedisStorage(redis_pool)
session_redis_middleware = aiohttp_session.session_middleware(storage)

middle = [
    session_middleware(EncryptedCookieStorage(hashlib.sha256(bytes(SECRET_KEY, 'utf-8')).digest())),
    authorize,
    session_redis_middleware
]

app = web.Application(middlewares=middle)

aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))

for route in routes:
    app.router.add_route(*route[:3], name=route[3])
app.router.add_static('/static', 'static', name='static')

app.client = ma.AsyncIOMotorClient(MONGO_HOST)
app.db = app.client[MONGO_DB_NAME]

app['static_root_url'] = '/static'
app['websockets'] = collections.defaultdict(list)
app['online'] = {}
app['models'] = {}
app['photo_dir'] = PHOTO_DIR
app['avatar_dir'] = AVATAR_DIR

app.on_startup.extend([
    create_models,
    create_redis,
    # start_background_tasks
])

app.on_cleanup.append([
    # cleanup_background_tasks,
    close_redis,
])

web.run_app(app)
