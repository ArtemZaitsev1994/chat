import logging
import os
from os.path import isfile
from envparse import env

log = logging.getLogger('app')
log.setLevel(logging.DEBUG)

f = logging.Formatter('[L:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', datefmt = '%d-%m-%Y %H:%M:%S')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(f)
log.addHandler(ch)

if isfile('.env'):
    env.read_envfile('.env')

DEBUG = env.bool('DEBUG', default=False)

SITE_HOST = env.str('HOST')
SITE_PORT = env.int('PORT')
SECRET_KEY = env.str('SECRET_KEY')
MONGO_HOST = 'mongodb'
# MONGO_HOST = os.getenv('MONGODB_URI')
MONGO_DB_NAME = env.str('MONGO_DB_NAME')

MESSAGE_COLLECTION = 'messages'
USER_COLLECTION    = 'users'
UNREAD_COLLECTION  = 'unread_message'
COMPANY_COLLECTION = 'company'
EVENT_COLLECTION   = 'event'
INVITE_COLLECTION  = 'invite'
NOTIFICATIOINS     = 'notifications'

BASEDIR = os.path.dirname(os.path.realpath(__file__))
PHOTO_DIR = os.path.join(BASEDIR, 'static/photo/')
AVATAR_DIR = os.path.join(BASEDIR, 'static/photo/users/')
