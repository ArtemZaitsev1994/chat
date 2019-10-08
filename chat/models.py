from datetime import datetime
from settings import MESSAGE_COLLECTION


class Message():

    def __init__(self, db, **kwargs):
        self.collection = db[MESSAGE_COLLECTION]

    async def save(self, user, msg, chat_name, **kw):
        result = await self.collection.insert({
            'user': user,
            'msg': msg,
            'time': datetime.now(),
            'chat_name': chat_name
        })
        return result

    async def get_messages(self, chat_name):
        messages = self.collection.find({'chat_name': chat_name}).sort([('time', 1)])
        return await messages.to_list(length=None)
