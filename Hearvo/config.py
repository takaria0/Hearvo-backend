import os
setting = os.environ['ENVIRONMENT']

API_VERSION = "v1.0"
URL_PREFIX = f"/api/{API_VERSION}"
SECRET_KET = os.environ["SECRET_KEY"]

DEFAULT_LIMIT = "3000/day;300/hour;30/minute;1/second"

POSTS_PER_PAGE = 20

MINIMUM_VOTES_TO_COMPUTE_CLOSE_USERS = os.environ.get("MINIMUM_VOTES_TO_COMPUTE_CLOSE_USERS", 10)
# from datetime import datetime, timedelta, timezone, timedelta, timezone
# JST = timezone(timedelta(hours=+9), 'JST')

if setting == "dev":
  ALLOW_ORIGIN_LIST = ["*"]

  user = os.environ['POSTGRES_USER']
  password = os.environ['POSTGRES_PASSWORD']
  host = os.environ['POSTGRES_HOST']
  db = os.environ['POSTGRES_DB']
  port = os.environ['POSTGRES_PORT']

  APP_PORT = int(os.environ.get('PORT', 8080))
  RECREATE_POLL_LIMIT_DAYS = os.environ['RECREATE_POLL_LIMIT_DAYS']
  DEBUG_SETTING = True

  SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}".format(
          user=user,
          password=password,
          host=host,
          port=port,
          database=db
      )

  cache_config = {
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 60 * 5, # sec
  }

elif setting == "prod":
  # ALLOW_ORIGIN_FRONT = os.environ["ALLOW_ORIGIN_FRONT"]
  ALLOW_ORIGIN_LIST = ["https://hearvo.com", "https://jp.hearvo.com", "https://us.hearvo.com"] # add later to enable cors access fron 

  APP_PORT = int(os.environ.get('PORT', 8080))
  RECREATE_POLL_LIMIT_DAYS = os.environ['RECREATE_POLL_LIMIT_DAYS']
  DEBUG_SETTING = False

  DATABASE_URL = os.environ['DATABASE_URL']
  if DATABASE_URL.startswith("postgres://"): # Heroku does not support ENV DATABASE_URL change 
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

  SQLALCHEMY_DATABASE_URI = DATABASE_URL
  
  MEMCACHIER_SERVERS = os.environ.get('MEMCACHIER_SERVERS')
  MEMCACHIER_USERNAME = os.environ.get('MEMCACHIER_USERNAME') or ''
  MEMCACHIER_PASSWORD = os.environ.get('MEMCACHIER_PASSWORD') or ''
  cache_config = {
    'CACHE_TYPE': 'saslmemcached',
    'CACHE_DEFAULT_TIMEOUT': 60 * 5, # sec
    'CACHE_MEMCACHED_SERVERS': MEMCACHIER_SERVERS.split(','),
    'CACHE_MEMCACHED_USERNAME': MEMCACHIER_USERNAME,
    'CACHE_MEMCACHED_PASSWORD': MEMCACHIER_PASSWORD,
    'CACHE_OPTIONS': { 'behaviors': {
        # Faster IO
        'tcp_nodelay': True,
        # Keep connection alive
        'tcp_keepalive': True,
        # Timeout for set/get requests
        'connect_timeout': 2000, # ms
        'send_timeout': 750 * 1000, # us
        'receive_timeout': 750 * 1000, # us
        '_poll_timeout': 2000, # ms
        # Better failover
        'ketama': True,
        'remove_failed': 1,
        'retry_timeout': 2,
        'dead_timeout': 30}
        }
                    }