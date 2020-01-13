from typing import Dict, Any

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session


class Search(web.View):

    @aiohttp_jinja2.template('features/search.html')
    async def get(self):
        data = self.request.get('data', {})
        item = self.request.rel_url.query.get('item')
        model = self.request.app['models'][item]
        items = await model.get_all()
        data.update({'item': True, 'items': items})
        return data
