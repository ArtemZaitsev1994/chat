from chat.views import ChatList, WebSocket, main_redirect, update_unread
from auth.views import Login, SignIn, SignOut, AccountDetails
from about.views import About
from company.views import Company, AllCompanys, MyCompany, check_access_to_company


routes = [
    ('GET',  '/',             main_redirect,  'main_redirect'),
    ('GET',  '/chat',         ChatList,       'main'),
    ('GET',  '/ws',           WebSocket,      'chat'),
    ('POST', '/update',       update_unread,  'update'),
    ('*',    '/login',        Login,          'login'),
    ('*',    '/signin',       SignIn,         'signin'),
    ('*',    '/signout',      SignOut,        'signout'),
    ('*',    '/account',      AccountDetails, 'account'),
    ('*',    '/about',        About,          'about_main'),
    ('*',    '/my_companys',  MyCompany,        'my_companys'),
    ('*',    '/all_companys', AllCompanys,    'all_companys'),
    ('*',    '/company',      Company,        'company'),
    ('POST', '/check_access_to_company', check_access_to_company, 'check_access_to_company')

]
