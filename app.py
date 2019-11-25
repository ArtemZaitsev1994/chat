import aioredis
import asyncio
import aiohttp_jinja2
import jinja2
import hashlib
import collections
import os
import aiohttp_session
import aio_pika

from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttp_session.redis_storage import RedisStorage
from aiohttp import web

from routes import routes
from middlewares import authorize
from motor import motor_asyncio as ma
from settings import *
from auth.models import User
from company.models import Company
from chat.models import UnreadMessage, Message
from events.models import Event, Photo
from invite.models import Invite


basedir = os.path.dirname(os.path.realpath(__file__))
photo_dir = os.path.join(basedir, 'static/photo/')
avatar_dir = os.path.join(basedir, 'static/photo/users/')

async def on_shutdown(app):
    for room in app['websockets']:
        [await ws.close(code=1001, mesage='Server shutdown') for ws in room]

async def create_models(app):
    app['models'].update({
        'user': User(app.db, {}),
        'unread': UnreadMessage(app.db),
        'message': Message(app.db),
        'company': Company(app.db),
        'event': Event(app.db),
        'photo': Photo(app.db),
        'invite': Invite(app.db)
    })

async def create_redis(app):
    app['redis'] = await aioredis.create_redis(('localhost', 6379))
    # app['redis'] = await aioredis.create_redis(('redis', 6379))

async def close_redis(app):
    app['redis'].close()
    await app['redis'].wait_closed()
    

async def make_redis_pool():
    redis_address = ('127.0.0.1', '6379')
    # redis_address = ('redis', '6379')
    return await aioredis.create_pool(
        redis_address,
        create_connection_timeout=1,
    )


async def listen_to_rabbit(app):
    connection = await aio_pika.connect_robust("amqp://guest:guest@127.0.0.1/", loop=app.loop)
    # connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/", loop=app.loop)
    async with connection:
        queue_name = 'chat'

        channel = await connection.channel()
        queue = await channel.declare_queue(
            queue_name,
            auto_delete=True
        )

        async with queue.iterator() as q_iter:
            print(4)
            async for mess in q_iter:
                print(mess)
                async with mess.process():
                    print(mess.body)


async def start_background_tasks(app):
    app['rabbit_listner'] = app.loop.create_task(listen_to_rabbit(app))

async def cleanup_background_tasks(app):
    app['rabbit_listner'].cancel()
    await app['rabbit_listner']

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
app['static_root_url'] = '/static'
app.router.add_static('/static', 'static', name='static')

app.client = ma.AsyncIOMotorClient(MONGO_HOST)
app.db = app.client[MONGO_DB_NAME]

app['websockets'] = collections.defaultdict(list)
app['online'] = {}
app['models'] = {}
app['photo_dir'] = photo_dir
app['avatar_dir'] = avatar_dir

app.on_startup.append(create_models)
app.on_startup.append(create_redis)
app.on_startup.append(start_background_tasks)

app.on_cleanup.append(cleanup_background_tasks)
app.on_cleanup.append(on_shutdown)
app.on_cleanup.append(close_redis)

web.run_app(app)
