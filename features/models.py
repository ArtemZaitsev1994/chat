from datetime import datetime
from bson.objectid import ObjectId
from settings import EVENT_COLLECTION


class Event:

    def __init__(self, db, **kw):
        self.db = db
        self.collection = self.db[EVENT_COLLECTION]

    async def get_event(self, _id, **kw):
        return await self.collection.find_one({'_id': ObjectId(_id)})

    async def get_event_by_name(self, name, **kw):
        return await self.collection.find_one({'name': name})

    async def create_event(self, data, admin_id, **kw):
        event = await self.get_event_by_name(data['name'])
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
        else:
            result = False
        return result

    async def add_photo(self, _id, photo_id):
        await self.collection.update_one({'_id': ObjectId(_id) }, {'$push': {'photo': photo_id}})

    async def add_avatar(self, _id, photo_id):
        await self.collection.update_one({'_id': ObjectId(_id) }, {'$set': {'avatar': photo_id}})

    async def get_events_by_comp(self, company_id, **kw):
        events = await self.collection.find({'company_id': company_id}).to_list(length=None)
        for e in events:
            e['_id'] = str(e['_id'])
        return events

    async def get_events_by_companys(self, company_list, **kw):
        events = await self.collection.find({'company_id': {'$in': company_list}}).sort([('_id', 1)]).to_list(length=None)
        for e in events:
            e['_id'] = str(e['_id'])
        return events

    # async def get_company_by_user(self, user_id, **kw):
    #     result =  await self.collection.find({'users': user_id}).to_list(length=None)
    #     return result

    # async def add_user_to_comp(self, _id, user_id):
    #     result = await self.collection.update(
    #         {'_id': ObjectId(_id) },
    #         {'$push': {'users': user_id}}
    #     )
    #     return result
        
    # async def delete_user_from_comp(self, _id, user_id):
    #     result = await self.collection.update(
    #         {'_id': ObjectId(_id) },
    #         {'$pull': {'users': user_id}}
    #     )
    #     return result

    async def delete(self, comp_id):
        result = await self.collection.delete_many({'_id': ObjectId(comp_id)})
        return result

    async def clear_db(self):
        await self.collection.drop()


class Photo:

    def __init__(self, db, **kw):
        self.db = db
        self.collection = self.db[EVENT_COLLECTION]

    async def get_photo(self, _id, **kw):
        return await self.collection.find_one({'_id': ObjectId(_id)})

    async def get_event_by_name(self, name, **kw):
        return await self.collection.find_one({'name': name})

    async def create_photo(self, event_id, **kw):
        now = datetime.now()
        result = await self.collection.insert({
            'date': now,
            'event_id': event_id,
        })
        return result

    async def create_avatar(self, user_id, **kw):
        result = await self.collection.insert({
            'user_id': user_id,
        })
        return result


    async def delete(self, comp_id):
        result = await self.collection.delete_many({'_id': ObjectId(comp_id)})
        return result

    async def clear_db(self):
        await self.collection.drop()
