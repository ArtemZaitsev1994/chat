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

    async def create_company(self, data, admin_id, login, **kw):
        company = await self.get_company_by_name(data['name'])
        if not company:
            result = await self.collection.insert({
                **data,
                'users': [(login, admin_id)],
                'admin_id': admin_id,
                'admin': login
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

    async def update_user(self, _id, data):
        result = await self.collection.replace_one(
            {'_id': ObjectId(_id) },
            data
        )
        return result

    async def clear_db(self):
        await self.collection.drop()
