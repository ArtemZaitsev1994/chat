from datetime import datetime
from bson.objectid import ObjectId
from settings import MESSAGE_COLLECTION, UNREAD_COLLECTION


class Message():
    """
    Класс сообщения в базе
    """

    def __init__(self, db, **kwargs):
        self.collection = db[MESSAGE_COLLECTION]

    async def save(self, from_user, msg, to_user, chat_name, **kw):
        """
        Сохранить сообщение приватного чата в базе

        Args:
            from_user - ID пользователя, от которого сообщение
            msg - текст сообщения
            to_user - ID пользователя, которому сообщение
            chat_name - название комнаты чата
        """
        result = await self.collection.insert({
            'from_user': str(from_user),
            'msg': msg,
            'time': datetime.now(),
            'to_user': str(to_user),
            'chat_name': chat_name,
        })
        return result

    async def save_for_company(self, from_user, msg, company_id):
        """
        Сохранить сообщение общего чата в базе

        Args:
            from_user - ID пользователя, от которого сообщение
            msg - текст сообщения
            company_id - ID компании
        """
        result = await self.collection.insert({
            'from_user': from_user,
            'msg': msg,
            'time': datetime.now(),
            'company_id': company_id
        })
        return result

    async def get_messages(self, chat_name):
        """
        Получить сообщения по имени чата

        Args:
            chat_name - название комнаты чата
        """
        messages = self.collection.find({'chat_name': chat_name}).sort([('time', 1)])
        return await messages.to_list(length=None)

    async def get_messages_by_company(self, company_id):
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
    """
    Класс с определеннием непрочитанных сообщений внутри одной чат-комнаты
    """

    def __init__(self, db, **kwargs):
        self.collection = db[UNREAD_COLLECTION]

    async def save(self, from_user, msg_id, to_user, **kw):
        """
        Сохранить сообщение общего чата в базе

        Args:
            from_user - ID пользователя, от которого сообщение
            msg_id - ID сообщения
            to_user - ID пользователя, которому сообщение
        """
        result = await self.collection.insert({
            'from_user': from_user,
            'msg_id': msg_id,
            'to_user': to_user,
            'count': 1
        })
        return result

    async def save_for_company(self, from_user, msg_id, to_company, **kw):
        """
        Сохранить сообщение общего чата в базе

        Args:
            from_user - ID пользователя, от которого сообщение
            msg_id - ID сообщения
            to_company - ID компании
        """
        result = await self.collection.insert({
            'from_user': from_user,
            'msg_id': msg_id,
            'to_company': to_company,
            'count': 1
        })
        return result

    async def get_unread(self, _id):
        """
        Получить сообщения по ID записи

        Args:
            _id - ID записи в базе
        """
        return await self.collection.find_one({'_id': _id})

    async def add_unread(self, _id):
        """
        увеличить счетчик непрочитанных сообщений внутри одной комнаты

        Args:
            _id - ID записи в базе
        """
        result = await self.collection.update(
            {'to_company': _id},
            {'$inc': {'count': 1}}
        )
        return result

    async def add_unread_user_chat(self, from_user, to_user):
        """
        увеличить счетчик непрочитанных сообщений внутри одной комнаты

        Args:
            from_user - ID пользователя, от которого сообщение
            to_user - ID пользователя которому сообщение
        """
        result = await self.collection.update(
            {'from_user': from_user, 'to_user': to_user},
            {'$inc': {'count': 1}}
        )
        return result

    async def count_unread(self, to_user):
        """
        увеличить счетчик непрочитанных сообщений внутри одной комнаты

        Args:
            to_user - ID пользователя которому сообщение
        """
        messages = await self.collection.find({'to_user': to_user}).to_list(length=None)
        result = {x['from_user']: x['count'] for x in messages}
        return result

    async def check_unread(self, company_id):
        """
        проверка, есть ли непрочитанные сообщения внутри общего чата компании

        Args:
            company_id - ID компании
        """
        return await self.collection.find_one({'to_company': company_id})

    async def get_unread_user_chat(self, from_user, to_user):
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

    async def delete(self, user_id, from_user):
        """
        удалить запись - ползователь прочитал сообщения

        Args:
            user_id - ID пользователя, который прочитал сообщения
            from_user - ID пользователя, чьи сообщения прочитали
        """
        await self.collection.delete_many({'to_user': user_id, 'from_user': from_user})

    async def delete_by_company(self, company_id):
        """
        удалить запись - сообщения в общем чате прочитаны

        Args:
            company_id - ID компании
        """
        await self.collection.delete_many({'to_company': company_id})

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


