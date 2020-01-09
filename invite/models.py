from datetime import datetime
from bson.objectid import ObjectId
from settings import INVITE_COLLECTION


class Invite:

    def __init__(self, db, **kw):
        self.db = db
        self.collection = self.db[INVITE_COLLECTION]

    async def get_invite(self, _id, **kw):
        return await self.collection.find_one({'_id': ObjectId(_id)})

    async def get_invite_to_company(self, user_id, company_id, **kw):
        return await self.collection.find_one({'user_id': user_id, 'company_id': company_id})

    async def create_invite(self, user_id, data):
        invite = await self.get_invite_to_company(user_id, data['company_id'])
        if not invite:
            result = await self.collection.insert({
                'user_id': user_id,
                'status': 'Ожидает',
                **data,
            })
        else:
            result = False
        return result

    async def get_invites_by_comp(self, company_id, status=None):
        if status:
            invites = await self.collection.find({
                'company_id': company_id,
                'status': status
            }).to_list(length=None)
        else:
            invites = await self.collection.find({'company_id': company_id}).to_list(length=None)
        for i in invites:
            i['_id'] = str(i['_id'])
        return invites

    async def get_invites_number(self, company_id, **kw):
        count = await self.collection.count({'company_id': company_id})
        return count

    async def decline_invite(self):
        return await self.collection.update_one(
            {'user_id': data['user_id'], 'company_id': data['company_id']},
            {'$set': {'status': 'Отклонено'}}
        )

    async def accept_invite(self):
        return await self.collection.update_one(
            {'user_id': data['user_id'], 'company_id': data['company_id']},
            {'$set': {'status': 'Принято'}}
        )

    async def delete(self, user_id, company_id):
        result = await self.collection.delete_many({'user_id': user_id, 'company_id': company_id})
        return result

    async def clear_db(self):
        await self.collection.drop()
