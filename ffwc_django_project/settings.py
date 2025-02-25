from django.contrib.staticfiles import handlers
from datetime import timedelta


from pathlib import Path
import os,json,pymysql
from corsheaders.defaults import default_headers

# import mimetypes
# mimetypes.add_type("text/css", ".css", True)


from import_export.formats.base_formats import CSV, XLSX
IMPORT_FORMATS = [CSV, XLSX]

SECURE_CROSS_ORIGIN_OPENER_POLICY = None

# extend StaticFilesHandler to add "Access-Control-Allow-Origin" to every response
class CORSStaticFilesHandler(handlers.StaticFilesHandler):
    def serve(self, request):
        response = super().serve(request)
        response['Access-Control-Allow-Origin'] = ['*',
        'https://ffwc-api.bdservers.site/admin/',
        'https://ffwc-api.bdservers.site/admin/login/',
        'https://ffwc-api.bdservers.site/admin/login/?next=/admin/login',

        ]
        return response

# 
# monkeypatch handlers to use our class instead of the original StaticFilesHandler
handlers.StaticFilesHandler = CORSStaticFilesHandler

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-&%+%gt$iqu^raos_nhr^62*bt8oj$ri3@c7nkypd9(n71-jx*p'

# DEBUG = True
DEBUG = True
ALLOWED_HOSTS = ['*']

# 'https://ffwc-api.bdservers.site',
# 'https://ffwc-api.bdservers.site/',
# 'https://ffwc-api.bdservers.site/admin/',
# 'https://ffwc-api.bdservers.site/admin/login/',
# 'https://ffwc-api.bdservers.site/admin/login/?next=/admin/login',
# 'https://ffwc-api.bdservers.site/admin/login/?next=/admin/'

CSRF_TRUSTED_ORIGINS =[
    'https://ffwc-api.bdservers.site',
    'https://ffwc-api.bdservers.site/',
    'https://ffwc-api.bdservers.site/admin/',
    'https://ffwc-api.bdservers.site/admin/login/',
    'https://ffwc-api.bdservers.site/admin/login/?next=/admin/login',
    'https://ffwc-api.bdservers.site/admin/login/?next=/admin/'
    ]

# APPEND_SLASH = False

CORS_ORIGIN_ALLOW_ALL = True
ROOT_URLCONF = 'ffwc_django_project.urls'

# Application definition
INSTALLED_APPS = [

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'import_export',

    'data_load.apps.DataLoadConfig',
    'earthEngine.apps.EarthengineConfig',
    'userauth.apps.UserauthConfig',
    'fileuploads.apps.FileuploadsConfig',

    'django_celery_results',
    'celery_progress',
    
    # Shaif added app
    'app_emails',
    'app_subscriptions',
    'app_dissemination',
]

REST_FRAMEWORK = {

# 'DEFAULT_PERMISSION_CLASSES': [
#    'rest_framework.permissions.AllowAny',
# ],

'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )

}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=50000),
    # "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=90),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,

    "ALGORITHM": "HS256",
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,

    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=50000),
    # "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),

    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

### ------------------------------------------------------- ###
### CORS CONFIGURATIONS
### ------------------------------------------------------- ###
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_METHODS = (
    '*'
)
CORS_ALLOW_HEADERS = (
    '*'
)
CORS_ALLOW_CREDENTIALS = True
X_FRAME_OPTIONS = 'ALLOWALL'
XS_SHARING_ALLOWED_METHODS = ['POST', 'GET', 'OPTIONS', 'PUT', 'DELETE']


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

WSGI_APPLICATION = 'ffwc_django_project.wsgi.application'
DATABASES = DATABASES = json.load(open(os.path.join(BASE_DIR,'dbconfig.json'),'r'))
pymysql.version_info = (1, 4, 3,"final", 0)
pymysql.install_as_MySQLdb()


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
DJANGO_CELERY_BEAT_TZ_AWARE = False

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static"),]


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_ROOT = os.path.join(BASE_DIR / 'assets')
MEDIA_URL = '/assets/'




# 👇 2. Add the following lines
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        # 'LOCATION': 'redis://127.0.0.1:6379',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

CELERY_BROKER_URL = "redis://127.0.0.1:6379/1"
# CELERY_BROKER_URL = "redis://127.0.0.1:6379"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND='django-db'
# CELERY_CACHE_BACKEND = 'django-cache''
# TIME_ZONE = 'Asia/Dhaka'



with open(BASE_DIR / 'env.json', 'r') as envf:
    env_ = json.load(envf)
### --------------------------------------------------------------- ###
### START Mail configuration
### --------------------------------------------------------------- ###
# EMAIL_CONFIG = env_['pending_user_mail_conf']
EMAIL_CONFIG = env_['pending_user_mail_conf']

EMAIL_BACKEND = EMAIL_CONFIG['EMAIL_BACKEND']
EMAIL_HOST = EMAIL_CONFIG['EMAIL_HOST']
EMAIL_USE_TLS = EMAIL_CONFIG['EMAIL_USE_TLS']   
EMAIL_PORT = EMAIL_CONFIG['EMAIL_PORT']
EMAIL_HOST_USER = EMAIL_CONFIG['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = EMAIL_CONFIG['EMAIL_HOST_PASSWORD'] 
### --------------------------------------------------------------- ###
### END Mail configuration
### --------------------------------------------------------------- ###