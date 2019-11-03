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
                **data,
            })
        else:
            result = False
        return result

    async def get_invites_by_comp(self, company_id, **kw):
        invites = await self.collection.find({'company_id': company_id}).to_list(length=None)
        for i in invites:
            i['_id'] = str(i['_id'])
        return invites

    async def delete(self, invite_id):
        result = await self.collection.delete_many({'_id': ObjectId(invite_id)})
        return result

    async def clear_db(self):
        await self.collection.drop()
