from typing import Dict, Any

import aio_pika
import aioredis
import json
from aiohttp.web_app import Application

from auth.models import User
from chat.models import UnreadMessage, Message
from company.models import Company
from events.models import Event, Photo
from invite.models import Invite


async def create_models(app: Application):
    app['models'].update({
        'message': Message(app.db),
        'company': Company(app.db),
        'unread': UnreadMessage(app.db),
        'invite': Invite(app.db),
        'event': Event(app.db),
        'photo': Photo(app.db),
        'user': User(app.db, {}),
    })


async def create_redis(app: Application):
    app['redis'] = await aioredis.create_redis(('localhost', 6379))
    app['redis'].decode_response = True
    # app['redis'] = await aioredis.create_redis(('redis', 6379))

async def close_redis(app: Application):
    app['redis'].close()
    await app['redis'].wait_closed()
    
async def make_redis_pool():
    redis_address = ('127.0.0.1', '6379')
    # redis_address = ('redis', '6379')
    return await aioredis.create_pool(
        redis_address,
        create_connection_timeout=1,
    )


async def listen_to_rabbit(app: Application):
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
            async for mess in q_iter:
                async with mess.process():
                    print(mess.body)

async def start_background_tasks(app: Application):
    app['rabbit_listner'] = app.loop.create_task(listen_to_rabbit(app))

async def cleanup_background_tasks(app: Application):
    app['rabbit_listner'].cancel()
    await app['rabbit_listner']


async def send_notification(app: Application, data: Dict[list, Any]):
    js_data = json.dumps(data)
    js_data = js_data.encode('utf-8').decode('utf8').replace("'", '"')
    

    await app['redis'].publish_json('notifications', js_data)
