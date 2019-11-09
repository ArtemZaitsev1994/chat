from bson.objectid import ObjectId
from settings import USER_COLLECTION


class User():

    def __init__(self, db, data, **kw):
        self.db = db
        self.collection = self.db[USER_COLLECTION]
        self.email = data.get('email')
        self.login = data.get('login')
        self.password = data.get('password')
        self.about = data.get('about', '')
        self.avatar = data.get('about', '')
        self.id = data.get('id')

    async def check_user(self, **kw):
        return await self.collection.find_one({'login': self.login})

    async def get_login(self, user_id, **kw):
        result =  await self.collection.find_one({'_id': ObjectId(user_id)})
        return result['login']

    async def get_user(self, user_id):
        return await self.collection.find_one({'_id': ObjectId(user_id)})

    async def get_logins(self, users_id, **kw):
        result = {str(x['_id']): x['login'] for x in await self.collection.find(
            {'_id':{'$in': [ObjectId(y) for y in users_id]}}
        ).to_list(length=None)}
        return result

    async def get_all_users(self, **kw):
        users = await self.collection.find().to_list(length=100)
        for u in users:
            u['_id'] = str(u['_id'])
        return users

    async def add_contact(self, user_id, _id):
        result = await self.collection.update(
            {'_id': ObjectId(user_id) },
            {'$addToSet': {'contacts': _id}}
        )
        return result

    async def delete_contact(self, user_id, _id):
        result = await self.collection.update(
            {'_id': ObjectId(user_id) },
            {'$pull': {'contacts': _id}},
        )
        return result

    async def get_users(self, users_list, **kw):
        result = await self.collection.find({'_id':{'$in': [ObjectId(y) for y in users_list]}}).to_list(length=None)
        return result


    async def create_user(self, **kw):
        user = await self.check_user()
        if not user:
            result = await self.collection.insert({
                'email': self.email,
                'login': self.login,
                'password': self.password,
                'about': self.about,
                'avatar': self.avatar,
                'contacts': [],
            })
        else:
            result = 'User exists'
        return result

    async def update_user(self, _id, data):
        result = await self.collection.update(
            {'_id': ObjectId(_id) },
            {'$set': data}
        )
        return result

    async def set_avatar(self, _id, photo_id):
        await self.collection.update_one({'_id': ObjectId(_id) }, {"$set": {'avatar': photo_id}})

    async def clear_db(self):
        await self.collection.drop()
