from chat.views import (
    ChatList, CompanyWebSocket, main_redirect,
    update_unread, UserChat, UserChatCompany,
    update_unread_company, CommonWebSocket
)
from auth.views import Login, SignIn, SignOut, AccountDetails
from about.views import About, drop_all
from company.views import Company, AllCompanys, MyCompany, check_access_to_company, CompanyDetails
from events.views import Event, CompEventList, CompEvent, Photo
from invite.views import Invite
from features.views import Search

routes = [
    ('GET',  '/',           main_redirect,    'main_redirect'),
    ('GET',  '/chat',       ChatList,         'chat_list'),
    ('GET',  '/ws_company', CompanyWebSocket, 'chat'),
    ('GET',  '/ws_common',  CommonWebSocket,  'common_websocket'),
    ('POST', '/update',     update_unread,    'update'),
    ('POST', '/user_chat',  UserChat,         'user_chat'),
    ('POST', '/user_chat_company',      UserChatCompany,       'user_chat_company'),
    ('POST', '/update_unread_company',  update_unread_company, 'update_unread_company'),

    ('*', '/login',   Login,          'login'),
    ('*', '/signin',  SignIn,         'signin'),
    ('*', '/signout', SignOut,        'signout'),
    ('*', '/account', AccountDetails, 'account'),


    ('*',    '/my_companys',     MyCompany,      'my_companys'),
    ('*',    '/news',            AllCompanys,    'all_companys'),
    ('*',    '/company',         Company,        'company'),
    ('*',    '/company_details', CompanyDetails, 'details'),
    ('POST', '/check_access_to_company', check_access_to_company, 'check_access_to_company'),

    ('*', '/event',           Event,         'event'),
    ('*', '/comp_event_list', CompEventList, 'comp_event_list'),
    ('*', '/comp_event',      CompEvent,     'comp_event'),
    ('*', '/photo',           Photo,         'photo'),
    ('*', '/user_avatar',     Photo,         'user_avatar'),

    ('*', '/invite', Invite, 'invite'),

    ('*', '/search', Search, 'search'),

    ('*',   '/about',    About,    'about_main'),
    # ОЧИСТКА БАЗЫ!!!!!!!!!!!
    ('GET', '/drop_all', drop_all, 'drop_all'),
]
