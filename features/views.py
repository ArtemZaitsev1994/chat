import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session


class Search(web.View):

    @aiohttp_jinja2.template('features/search.html')
    async def get(self):
        item = self.request.rel_url.query.get('item')
        model = self.request.app['models'][item]
        items = await model.get_all()
        session = await get_session(self.request)
        login = session.get('login')
        self_id = session.get('self_id')
        data = {item: True, 'items': items, 'own_login': login, 'self_id': self_id}
        return data
