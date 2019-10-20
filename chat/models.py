from datetime import datetime
from bson.objectid import ObjectId
from settings import MESSAGE_COLLECTION, UNREAD_COLLECTION


class Message():

    def __init__(self, db, **kwargs):
        self.collection = db[MESSAGE_COLLECTION]

    async def save(self, from_user, msg, company_id, **kw):
        result = await self.collection.insert({
            'from_user': from_user,
            'msg': msg,
            'time': datetime.now(),
            'company_id': company_id
        })
        return result

    async def get_messages(self, chat_name):
        messages = self.collection.find({'chat_name': chat_name}).sort([('time', 1)])
        return await messages.to_list(length=None)

    async def get_messages_by_company(self, company_id):
        messages = self.collection.find({'company_id': company_id}).sort([('time', 1)])
        return await messages.to_list(length=None)


    async def clear_db(self):
        await self.collection.drop()


class UnreadMessage():

    def __init__(self, db, **kwargs):
        self.collection = db[UNREAD_COLLECTION]

    async def save(self, from_user, msg_id, to_company, **kw):
        result = await self.collection.insert({
            'from_user': from_user,
            'msg_id': msg_id,
            'to_company': to_company,
            'count': 1
        })
        return result

    async def get_unread(self, _id):
        return await self.collection.find_one({'_id': _id})

    async def add_unread(self, _id):
        result = await self.collection.update(
            {'to_company': _id},
            {'$inc': {'count': 1}}
        )
        return result


    async def get_messages_from_main(self, user_id):
        messages = self.collection.find({'chat_name': 'main'}, )
        return await messages.to_list(length=None)

    async def check_unread(self, company_id):
        return await self.collection.find_one({'to_company': company_id})

    async def get_messages_recieved(self, user_id):
        messages = self.collection.find({'to_user': user_id})
        return await messages.to_list(length=None)

    async def get_messages_sent(self, user_id):
        messages = self.collection.find({'from_user': user_id})
        return await messages.to_list(length=None)

    async def delete(self, chat_name, user_id):
        await self.collection.delete_many({'chat_name': chat_name, 'to_user': user_id})

    async def clear_db(self):
        await self.collection.drop()

    async def get_mess_by_comp(self, user_id, comp):
        result = {}
        for c in comp:
            result[c['name']] = len(await self.collection.find({
                'chat_name': c['name'],
                'to_user': user_id,
            }).to_list(length=None))
        return result


