from typing import Dict, Any, List
from datetime import datetime

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from settings import EVENT_COLLECTION


class Event:

    def __init__(self, db: AsyncIOMotorDatabase, **kw):
        self.db = db
        self.collection = self.db[EVENT_COLLECTION]

    async def get_event(self, _id: str, **kw) -> Dict[str, Any]:
        return await self.collection.find_one({'_id': ObjectId(_id)})

    async def get_event_by_name(self, name: str, **kw) -> Dict[str, Any]:
        return await self.collection.find_one({'name': name})

    async def create_event(self, data: Dict[str, Any], admin_id: str, **kw) -> bool:
        event = await self.get_event_by_name(data['name'])
        result = False
        if not event:
            company_id = data.pop('company_id')
            date = [int(x) for x in data.pop('date').split('-')]
            if 'time' in data:
                date.extend([int(x) for x in data.pop('time').split(':')])
            date = datetime(*date)

            result = await self.collection.insert({
                **data,
                'company_id': company_id,
                'users': [admin_id],
                'admin_id': admin_id,
                'photo': [],
                'avatar': '',
                'date': date,

            })
        return result

    async def add_photo(self, _id: str, photo_id: str) -> bool:
        return await self.collection.update_one({'_id': ObjectId(_id) }, {'$push': {'photo': photo_id}})

    async def add_avatar(self, _id: str, photo_id: str) -> bool:
        return await self.collection.update_one({'_id': ObjectId(_id) }, {'$set': {'avatar': photo_id}})

    async def get_events_by_comp(self, company_id: str, **kw) -> List[Dict[str, Any]]:
        events = await self.collection.find({'company_id': company_id}).to_list(length=None)
        for e in events:
            e['_id'] = str(e['_id'])
        return events

    async def get_events_by_companys(self, company_list: str, **kw) -> List[Dict[str, Any]]:
        events = await self.collection.find({'company_id': {'$in': company_list}}).sort([('_id', 1)]).to_list(length=None)
        for e in events:
            e['_id'] = str(e['_id'])
        return events

    async def delete(self, comp_id: str) -> bool:
        result = await self.collection.delete_many({'_id': ObjectId(comp_id)})
        return result

    async def clear_db(self):
        await self.collection.drop()


class Photo:

    def __init__(self, db: AsyncIOMotorDatabase, **kw):
        self.db = db
        self.collection = self.db[EVENT_COLLECTION]

    async def get_photo(self, _id: str, **kw) -> Dict[str, Any]:
        return await self.collection.find_one({'_id': ObjectId(_id)})

    async def get_event_by_name(self, name: str, **kw) -> Dict[str, Any]:
        return await self.collection.find_one({'name': name})

    async def create_photo(self, event_id: str, **kw) -> bool:
        now = datetime.now()
        result = await self.collection.insert({
            'date': now,
            'event_id': event_id,
        })
        return result

    async def create_avatar(self, user_id: str, **kw) -> bool:
        result = await self.collection.insert({
            'user_id': user_id,
        })
        return result


    async def delete(self, comp_id: str):
        result = await self.collection.delete_many({'_id': ObjectId(comp_id)})
        return result

    async def clear_db(self):
        await self.collection.drop()
