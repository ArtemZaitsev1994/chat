import logging
import argparse
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

if isfile('.env'):
    env.read_envfile('.env')

    DEBUG = env.bool('DEBUG', default=False)

    SITE_HOST = env.str('HOST')
    SITE_PORT = env.int('PORT')
    SECRET_KEY = env.str('SECRET_KEY')

    MONGO_HOST = os.getenv('MONGO_HOST')
    MONGO_DB_NAME = env.str('MONGO_DB_NAME')

    REDIS_HOST = env.tuple('REDIS_HOST')
else:
    raise SystemExit('Create an env-file please.!')
    

parser = argparse.ArgumentParser()
parser.add_argument("--local", help="Send true if app starting localy")
args = parser.parse_args()

if args.local:
    REDIS_HOST = ('127.0.0.1', '6379')
    MONGO_HOST = 'mongodb://127.0.0.1:27017'
    print("Docker sucks?!")