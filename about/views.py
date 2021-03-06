import aiohttp_jinja2
import aiosmtplib

from aiohttp import web
from email.mime.text import MIMEText

from auth.models import User


class About(web.View):
    @aiohttp_jinja2.template('about/about.html')
    async def get(self):
        data = self.request.get('data', {})
        PHOTO_PATH = 'photo/main.gif'

        user = self.request.app['models']['user']
        users = await user.get_all_users()

        data['users'] = users
        data['photo_path'] = PHOTO_PATH,
        
        return data

    async def post(self):
        data = await self.request.json()
        message = MIMEText("Sent via aiosmtplib")
        message["From"] = "root@localhost"
        message["To"] = "artz1994@mail.ru"
        message["Subject"] = f'{data["message"]}\n\n\n\n\n\n{data["callback"]}'
        server = aiosmtplib.SMTP('smtp.gmail.com', 587)
        # TODO:
        await server.connect()
        await server.ehlo()
        await server.starttls()
        await server.login("tuse.web1@gmail.com", "TUSE_web1")
        text = message.as_string()
        await server.sendmail("tuse.web1@gmail.com", 'tuse.web1@gmail.com', text)
        # print(await aiosmtplib.send(message, hostname="smtp.mail.ru", port=465, username='tuse.web1@gmail.ru', password='TUSE_web1'))
        return web.json_response(True)


async def drop_all(request, data):
    data = self.request.get('data', {})

    models = {
        'user': request.app['models']['user'],
        'chat': request.app['models']['message'],
        'unread': request.app['models']['unread'],
        'event': request.app['models']['event'],
        'company': request.app['models']['company'],
        'photo': request.app['models']['photo'],
    }
    [await i.clear_db() for i in models.values()]

    leo = User(request.app.db, {'login': 'Leo', 'email': 'leo@mail.ru', 'password': 'qwe123'})
    lana = User(request.app.db, {'login': 'Lana', 'email': 'delRay@mail.ru', 'password': 'qwe123'})
    artem = User(request.app.db, {'login': 'Artem', 'email': 'artz1994@mail.ru', 'password': 'qwe123'})
    await leo.create_user()
    await lana.create_user()
    await artem.create_user()
