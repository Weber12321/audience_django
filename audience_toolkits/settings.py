"""
Django settings for audience_toolkits project.

Generated by 'django-admin startproject' using Django 3.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
from pathlib import Path
import pymysql
import environ
from corsheaders.defaults import default_headers

pymysql.install_as_MySQLdb()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'gemt7w)9ay($n(wbnj0*7t2g-f@^*q$z2-fuob)drj&0mkc=ls'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

URL_PREFIX = '/audience'

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'home.apps.HomeConfig',
    'documenting_jobs.apps.DocumentingJobsConfig',
    'labeling_jobs.apps.LabelingJobsConfig',
    'predicting_jobs.apps.PredictingJobsConfig',
    'modeling_jobs.apps.ModelingJobsConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_q',
    'corsheaders',
    'rest_framework',
    'django_filters',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
CORS_ALLOW_HEADERS = ('x-csrftoken', 'authorization', 'content-type', 'Access-Control-Allow-Origin')

CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = 'audience_toolkits.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ]
        ,
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

WSGI_APPLICATION = 'audience_toolkits.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

if not DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    env = environ.Env()
    env.read_env((BASE_DIR / '.env').open())
    # read from .env
    DATABASES = {
        'default': {
            'ENGINE': env("DATABASE_ENGINE"),
            'NAME': env("DATABASE_NAME"),  # 目標資料庫的名稱
            'USER': env("DATABASE_USER"),  # 資料庫帳號
            'PASSWORD': env("DATABASE_PASSWORD"),  # 資料庫密碼
            'HOST': env("DATABASE_HOST"),  # 主機位置，可以先測本地localhost
            'PORT': env("DATABASE_PORT"),
        }
    }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'normal': {
            'format': '[%(levelname)s] %(asctime)s | %(name)s:%(lineno)d | %(message)s'
        },
        'simple': {
            'format': '[%(levelname)s] %(message)s'
        },
    },
    # 'filters': {
    #     'require_debug_true': {
    #         '()': 'django.utils.log.RequireDebugTrue',
    #     },
    # },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',  # Default logs to stderr
            'formatter': 'normal',  # use the above "normal" formatter
            # 'filters': ['require_debug_true'],  # add filters
        },
    },
    'loggers': {
        '': {  # means "root logger"
            'handlers': ['console'],  # use the above "console" handler
            'level': 'DEBUG',  # logging level
        },
        'some_app.some_module': {  # Modify logger in some modules
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_datatables.renderers.DatatablesRenderer',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework_datatables.filters.DatatablesFilterBackend',
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework_datatables.pagination.DatatablesPageNumberPagination',
    'PAGE_SIZE': 10,
}

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'zh-hant'

TIME_ZONE = 'Asia/Taipei'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = URL_PREFIX + '/static/'
STATIC_ROOT = BASE_DIR / 'static'  # production時，呼叫 python manage.py collectstatic 統整靜態檔案輸出位置
LOGIN_URL = URL_PREFIX + '/accounts/login/'
LOGIN_REDIRECT_URL = URL_PREFIX + '/dashboard/'
LOGOUT_REDIRECT_URL = URL_PREFIX + '/'

STATICFILES_DIRS = [
    BASE_DIR / 'staticfiles',
]
# tmp files
UPLOAD_FILE_DIRECTORY = 'upload_files'
SAMPLE_DATA_FILE_DIRECTORY = 'sample_data_files'
# ======================================
#           django-Q settings
# ======================================
Q_CLUSTER = {
    'name': 'audience_toolkits',
    'workers': 1,
    'timeout': 10000,
    'retry': 12000,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default'
}

# ======================================
#     ML Model Settings Task settings
# ======================================

MODEL_PATH_FIELD_DIRECTORY = 'model_files'
ML_MODELS = {
    # "DUMMY_MODEL": {
    #     'verbose_name': '假模型',
    #     'module': 'core.audience.models.base_model.DummyModel',
    # },
    "SVM_MODEL": {
        'verbose_name': 'SVM',
        'module': 'core.audience.models.classic.svm_model.SvmModel',
    },
    "RANDOM_FOREST_MODEL": {
        'verbose_name': '隨機森林',
        'module': 'core.audience.models.classic.random_forest_model.RandomForestModel',
    },
    "KEYWORD_MODEL": {
        'verbose_name': '關鍵字規則',
        'module': 'core.audience.models.rule_base.keyword_base_model.KeywordModel',
    },
    "REGEX_MODEL": {
        'verbose_name': '正則表達式比對',
        'module': 'core.audience.models.rule_base.regex_model.RegexModel',
    },
    "TERM_WEIGHT_MODEL": {
        'verbose_name': '詞彙權重模型',
        'module': 'core.audience.models.classic.term_weight_model.TermWeightModel',
    },
}

# ======================================
#     Audience Labeler Task settings
# ======================================
# logger
VERBOSE_DEBUG_MESSAGE = True
LOG_FILE_DIRECTORY = BASE_DIR / 'logs'
LOG_BACKUP_COUNT = 30  # days
LOGGING_FORMAT = "[%(asctime)s][{_context}][%(levelname)s]: %(message)s"
LOGGING_ERROR_FORMAT = "[%(asctime)s][{_context}][%(funcName)s()][%(levelname)s]: %(message)s"

# content processing
STOP_WORD_DIR = []

# DEEPNLP APIs
DEEPNLP_POS_API = "http://rd2demo.eland.com.tw/segment"
DEEPNLP_POS_API_TOKEN = ""

# other
TEMP_DIR = BASE_DIR / 'tmp'

# predicting_result
FETCH_COUNT = -1
CONNECT_RETRIES = 3
# 若要新增AVAILABLE_FIELDS請同步調整 core.dao.input_example，key必須與InputExample對齊（會以getattr(key必須與InputExample對齊, key)取值）。
AVAILABLE_FIELDS = {
    'id': '文章id',
    's_id': '來源',
    's_area_id': '來源網站',
    'title': '標題',
    'author': '作者',
    'content': '內文',
    'post_time': '發文時間',
}
PREDICT_DATABASE = {
    'source': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'audience-source',  # 目標資料庫的名稱
        'USER': 'root',  # 資料庫帳號
        'PASSWORD': 'password',  # 資料庫密碼
        'HOST': 'localhost',  # 主機位置，可以先測本地localhost
        'PORT': '3306',
        'SCHEMA': 'wh_bbs_01',
        'TABLE': 'ts_page_content',
    },
    'result': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'audience-result',  # 目標資料庫的名稱
        'USER': 'root',  # 資料庫帳號
        'PASSWORD': 'password',  # 資料庫密碼
        'HOST': 'localhost',  # 主機位置，可以先測本地localhost
        'PORT': '3306',
    }
}

# ======================================
#     Audience API settings
# ======================================
env = environ.Env()
if env('PREDICT_ENV') == 'production':
    IS_PRODUCTION = True
else:
    IS_PRODUCTION = False
PORT = 8000

if IS_PRODUCTION:
    API_PATH = f'http://172.18.20.190:{PORT}'
else:
    API_PATH = f'http://127.0.0.1:{PORT}'

API_HEADERS = {
  'accept': 'application/json',
}

MODEL_TYPE = 'keyword_model'

PREDICT_TYPE = 'author_name'

OUTPUT_DB = 'audience_result'

# ======================================
#              doccano
# ======================================
if IS_PRODUCTION:
    DOCCANO_PATH = f'https://rd2demo.eland.com.tw/'
else:
    DOCCANO_PATH = f'http://127.0.0.1'



# ---- mixed content debug ----
# 因應 labeling_jobs api/jobs 在網頁中翻頁會發生 mixed content error 帶入錯誤的 domain host
# 加入以下設定强制產品端翻頁域名要與產品端域名一致
# 產品端部署 base.html head 要加上 <meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests"> 才能轉換標頭

if IS_PRODUCTION:
    secure_scheme_headers = {
        'X-FORWARDED-PROTOCOL': 'ssl',
        'X-FORWARDED-PROTO': 'https',
        'X-FORWARDED-SSL': 'on'}

    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('X-FORWARDED-PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    USE_X_FORWARDED_HOST = False
    SECURE_PROXY_SSL_HEADER = None
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
