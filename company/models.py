from typing import Dict, List, Any

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from settings import COMPANY_COLLECTION


class Company():

    def __init__(self, db: AsyncIOMotorDatabase, **kw):
        self.db = db
        self.collection = self.db[COMPANY_COLLECTION]

    async def get_company(self, _id: str, **kw) -> Dict[str, Any]:
        return await self.collection.find_one({'_id': ObjectId(_id)})

    async def get_companys_by_user(self, user_id: str) -> List[Any]:
        result = await self.collection.find({'users':{'$in': [user_id]}, 'admin_id': {'$ne': user_id}}).to_list(length=None)
        return result

    async def get_own_companys(self, user_id: str) -> List[Dict[str, Any]]:
        result = await self.collection.find({'admin_id': user_id}).to_list(length=None)
        return result

    async def get_company_by_name(self, name: str, **kw) -> Dict[str, Any]:
        return await self.collection.find_one({'name': name})

    async def check_access(self, company_id: str, user_id: str) -> bool:
        company = await self.get_company(company_id)
        return company and user_id == company['admin_id']

    async def create_company(self, data: str, admin_id: str, **kw) -> bool:
        company = await self.get_company_by_name(data['name'])
        result = False
        if not company:
            result = await self.collection.insert({
                **data,
                'users': [admin_id],
                'admin_id': admin_id
            })
        return result

    async def get_all(self, **kw) -> List[Dict[str, Any]]:
        companys = await self.collection.find().to_list(length=None)
        for c in companys:
            c['_id'] = str(c['_id'])
        return companys

    async def get_company_by_user(self, user_id: str, **kw) -> List[Dict[str, Any]]:
        result =  await self.collection.find({'users': user_id}).to_list(length=None)
        return result

    async def add_user_to_comp(self, _id: str, user_id: str) -> bool:
        result = await self.collection.update(
            {'_id': ObjectId(_id) },
            {'$push': {'users': user_id}}
        )
        return result
        
    async def delete_user_from_comp(self, _id: str, user_id: str) -> bool:
        result = await self.collection.update(
            {'_id': ObjectId(_id) },
            {'$pull': {'users': user_id}}
        )
        return result

    async def delete(self, comp_id: str) -> bool:
        result = await self.collection.delete_many({'_id': ObjectId(comp_id)})
        return result

    async def clear_db(self):
        await self.collection.drop()
