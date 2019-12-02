from datetime import datetime
from typing import List, Dict, Any

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from settings import MESSAGE_COLLECTION, UNREAD_COLLECTION


class Message():
    """
    Класс сообщения в базе
    """

    def __init__(self, db: AsyncIOMotorDatabase, **kwargs):
        self.collection = db[MESSAGE_COLLECTION]


    async def save(self, from_user: str, msg: str, to_user: str, chat_name: str) -> bool:
        """
        Сохранить сообщение приватного чата в базе

        Args:
            from_user - ID пользователя, от которого сообщение
            msg       - текст сообщения
            to_user   - ID пользователя, которому сообщение
            chat_name - название комнаты чата
        """
        result = await self.collection.insert({
            'from_user': from_user,
            'msg': msg,
            'time': datetime.now(),
            'to_user': to_user,
            'chat_name': chat_name,
        })
        return result


    async def save_for_company(self, from_user: str, msg: str, company_id: str) -> bool:
        """
        Сохранить сообщение общего чата в базе

        Args:
            from_user  - ID пользователя, от которого сообщение
            msg        - текст сообщения
            company_id - ID компании
        """
        result = await self.collection.insert({
            'from_user': from_user,
            'msg': msg,
            'time': datetime.now(),
            'company_id': company_id
        })
        return result


    async def get_messages(self, chat_name: str) -> List[Dict[str, Any]]:
        """
        Получить сообщения по имени чата

        Args:
            chat_name - название комнаты чата
        """
        messages = self.collection.find({'chat_name': chat_name}).sort([('time', 1)])
        return await messages.to_list(length=None)


    async def get_messages_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        """
        Получить сообщения по ID компании

        Args:
            company_id - ID компании
        """
        messages = self.collection.find({'company_id': company_id}).sort([('time', 1)])
        return await messages.to_list(length=None)


    async def clear_db(self):
        await self.collection.drop()


class UnreadMessage():
    """Класс с определеннием непрочитанных сообщений внутри одной чат-комнаты"""

    def __init__(self, db: AsyncIOMotorDatabase, **kwargs):
        self.collection = db[UNREAD_COLLECTION]


    async def save(self, from_user: str, msg_id: str, to_user: str) -> bool:
        """
        Сохранить сообщение общего чата в базе

        Args:
            from_user - ID пользователя, от которого сообщение
            msg_id    - ID сообщения
            to_user   - ID пользователя, которому сообщение
        """
        result = await self.collection.insert({
            'from_user': from_user,
            'msg_id': msg_id,
            'to_user': to_user,
            'count': 1
        })
        return result


    async def save_for_company(self, to_user, msg_id, to_company):
        """
        Сохранить сообщение общего чата в базе

        Args:
            to_user    - ID пользователя, от которого сообщение
            msg_id     - ID сообщения
            to_company - ID компании
        """
        result = await self.collection.insert({
            'msg_id': msg_id,
            'to_company': to_company,
            'to_user': to_user,
            'count': 1
        })
        return result


    async def get_unread(self, _id: ObjectId) -> Dict[str, Any]:
        """
        Получить сообщения по ID записи

        Args:
            _id - ID записи в базе
        """
        return await self.collection.find_one({'_id': _id})


    async def add_unread(self, _id: str, user_id: str) -> bool:
        """
        Увеличить счетчик непрочитанных сообщений внутри одной комнаты компании у одного пользователя

        Args:
            _id     - ID компании
            user_id - ID участника компании, получатель
        """
        result = await self.collection.update(
            {'to_company': _id, 'to_user': user_id},
            {'$inc': {'count': 1}}
        )
        return result


    async def add_unread_user_chat(self, from_user: str, to_user: str) -> bool:
        """
        увеличить счетчик непрочитанных сообщений внутри одной комнаты пользователя

        Args:
            from_user - ID пользователя, от которого сообщение
            to_user   - ID пользователя, которому сообщение
        """
        result = await self.collection.update(
            {'from_user': from_user, 'to_user': to_user},
            {'$inc': {'count': 1}}
        )
        return result


    async def count_unread(self, to_user: str, to_company: str) -> int:
        """
        Получить количество непрочитанных сообщений у пользователя внутри общего чата компании

        Args:
            to_user - ID пользователя которому сообщение
        """
        messages = await self.collection.find({'to_user': to_user, 'to_company': to_company}).to_list(length=None)
        return messages['count']


    async def check_unread(self, company_id: str, to_user: str) -> bool:
        """
        проверка, есть ли непрочитанные сообщения внутри общего чата компании

        Args:
            company_id - ID компании
        """
        return await self.collection.find_one({'to_company': company_id, 'to_user': to_user})


    async def get_unread_user_chat(self, from_user: str, to_user: str) -> Dict[str, Any]:
        """
        получить запись о непрочитанных сообщениях

        Args:
            from_user - ID пользователя, от которого сообщение
            to_user - ID пользователя которому сообщение
        """
        return await self.collection.find_one({'to_user': to_user, 'from_user': from_user})


    async def get_messages_recieved(self, user_id):
        # TODO: удалить
        messages = self.collection.find({'to_user': user_id})
        return await messages.to_list(length=None)


    async def get_messages_sent(self, user_id):
        # TODO: удалить
        messages = self.collection.find({'from_user': user_id})
        return await messages.to_list(length=None)


    async def delete(self, user_id: str, from_user: str) -> bool:
        """
        удалить запись - ползователь прочитал сообщения

        Args:
            user_id - ID пользователя, который прочитал сообщения
            from_user - ID пользователя, чьи сообщения прочитали
        """
        return await self.collection.update(
            {'from_user': from_user, 'to_user': user_id},
            {'$inc': {'count': 1}}
        )


    async def delete_by_company(self, company_id: str, user_id: str) -> bool:
        """
        удалить запись - сообщения в общем чате прочитаны

        Args:
            company_id - ID компании
        """
        return await self.collection.update(
            {'to_company': company_id, 'to_user': user_id},
            {'count': 0}
        )


    async def find_last_unread(self, company_id: str, self_id: str) -> bool:
        """
        Ищем хотя бы одним юзером прочитанные сообщения

        Args:
            company_id: ID компании
            user_id: ID юзера отправителя
        """
        if not await self.collection.find_one({'to_company': company_id, 'count': 0}):
            mess = await self.collection.find({'to_company': company_id}).sort([('count', 1)]).to_list(length=None)

            if len(mess) > 0:
                return mess[0]['count']
        return 0


    async def get_mess_by_comp(self, user_id: str, comp: str) -> Dict[str, Any]:
        result = {}
        for c in comp:
            result[c['name']] = len(await self.collection.find({
                'chat_name': c['name'],
                'to_user': user_id,
            }).to_list(length=None))
        return result


    async def clear_db(self):
        await self.collection.drop()
