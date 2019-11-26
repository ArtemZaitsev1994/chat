from typing import List, Dict, Any

from bson.objectid import ObjectId

from settings import USER_COLLECTION


class User():

    def __init__(self, db: TODO, data: Dict[str, Any], **kw):
        self.db = db
        self.collection = self.db[USER_COLLECTION]
        self.email = data.get('email')
        self.login = data.get('login')
        self.password = data.get('password')
        self.about = data.get('about', '')
        self.avatar = data.get('about', '')
        self.id = data.get('id')

    async def check_user(self, **kw) -> TODO:
        """Проверка существования юзера"""
        return await self.collection.find_one({'login': self.login})

    async def get_login(self, user_id: str, **kw) -> str:
        """
        Получить логин пользователя

        Args:
            user_id - ID пользователя
        """
        result =  await self.collection.find_one({'_id': ObjectId(user_id)})
        return result['login']

    async def get_user(self, user_id: str) -> TODO:
        """
        Получить пользователя по ID

        Args:
            user_id - ID пользователя
        """
        return await self.collection.find_one({'_id': ObjectId(user_id)})

    async def get_logins(self, users_id: str, **kw) -> Dict[str, str]:
        """
        Получить словарь логинов(value) по ID пользователей(key)

        Args:
            user_id - ID пользователя
        """
        result = {str(x['_id']): x['login'] for x in await self.collection.find(
            {'_id':{'$in': [ObjectId(y) for y in users_id]}}
        ).to_list(length=None)}
        return result

    async def get_all_users(self, **kw) -> List[Any]:
        """Получить всех пользователей в системе"""
        users = await self.collection.find().to_list(length=100)
        for u in users:
            u['_id'] = str(u['_id'])
        return users

    async def add_contact(self, user_id, _id) -> bool:
        """
        Получить добавить контакт к пользователю

        Args:
            user_id - ID пользователя
            _id     - ID контакта
        """
        result = await self.collection.update(
            {'_id': ObjectId(user_id) },
            {'$addToSet': {'contacts': _id}}
        )
        return result

    async def delete_contact(self, user_id, _id) -> bool:
        """
        Удалить контакт у пользователя

        Args:
            user_id - ID пользователя
            _id     - ID контакта
        """
        result = await self.collection.update(
            {'_id': ObjectId(user_id) },
            {'$pull': {'contacts': _id}},
        )
        return result

    async def get_users(self, users_list: list, **kw) -> List[TODO]:
        """
        Получить список юзеров по списку ID

        Args:
            users_list - список ID пользователей
        """
        result = await self.collection.find({'_id':{'$in': [ObjectId(y) for y in users_list]}}).to_list(length=None)
        return result


    async def create_user(self, **kw) -> bool:
        """Создание пользователя на основе экземпляра класса"""
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

    async def update_user(self, _id: str, data: Dict[str, Any]) -> bool:
        """
        Обновляем пользовательские данные

        Args:
            _id  - ID пользователя
            data - данные пользователя
        """
        result = await self.collection.update(
            {'_id': ObjectId(_id) },
            {'$set': data}
        )
        return result

    async def set_avatar(self, _id: str, photo_id: str) -> bool:
        """
        Задать аватар для пользователя

        Args:
            _id      - ID пользователя
            photo_id - ID фотографии
        """
        return await self.collection.update_one({'_id': ObjectId(_id) }, {"$set": {'avatar': photo_id}})

    async def clear_db(self):
        """Удалить все записи в коллекции БД"""
        await self.collection.drop()
