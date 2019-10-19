from bson.objectid import ObjectId
from settings import COMPANY_COLLECTION


class Company():

    def __init__(self, db, **kw):
        self.db = db
        self.collection = self.db[COMPANY_COLLECTION]

    async def get_company(self, _id, **kw):
        return await self.collection.find_one({'_id': ObjectId(_id)})

    async def get_company_by_name(self, name, **kw):
        return await self.collection.find_one({'name': name})

    async def create_company(self, data, admin_id, **kw):
        company = await self.get_company_by_name(data['name'])
        if not company:
            result = await self.collection.insert({
                **data,
                'users': [admin_id],
                'admin_id': admin_id
            })
        else:
            result = False
        return result

    async def get_all_comp(self, **kw):
        companys = await self.collection.find().to_list(length=None)
        for c in companys:
            c['_id'] = str(c['_id'])
        return companys

    async def get_company_by_user(self, user_id, **kw):
        result =  await self.collection.find({'users': user_id}).to_list(length=None)
        return result

    async def add_user_to_comp(self, _id, user_id):
        result = await self.collection.update(
            {'_id': ObjectId(_id) },
            {'$push': {'users': user_id}}
        )
        return result
        
    async def delete_user_from_comp(self, _id, user_id):
        result = await self.collection.update(
            {'_id': ObjectId(_id) },
            {'$pull': {'users': user_id}}
        )
        return result

    async def delete(self, comp_id):
        result = await self.collection.delete_many({'_id': ObjectId(comp_id)})
        return result

    async def clear_db(self):
        await self.collection.drop()
