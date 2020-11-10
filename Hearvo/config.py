import os
setting = os.environ['ENVIRONMENT']

API_VERSION = "v1.0"
URL_PREFIX = f"/api/{API_VERSION}"
SECRET_KET = os.environ["SECRET_KEY"]


if setting == "dev":
  ALLOW_ORIGIN_LIST = ["*"]

  user = os.environ['POSTGRES_USER']
  password = os.environ['POSTGRES_PASSWORD']
  host = os.environ['POSTGRES_HOST']
  db = os.environ['POSTGRES_DB']
  port = os.environ['POSTGRES_PORT']

  APP_PORT = int(os.environ.get('PORT', 8080))
  DEBUG_SETTING = True

  SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}".format(
          user=user,
          password=password,
          host=host,
          port=port,
          database=db
      )

elif setting == "prod":
  ALLOW_ORIGIN_LIST = [""] # add later to enable cors access fron frontend

  db_user = os.environ.get("DB_USER")
  db_pass = os.environ.get("DB_PASS")
  db_name = os.environ.get("DB_NAME")
  cloud_sql_connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME")

  DEBUG_SETTING = False


  SQLALCHEMY_DATABASE_URI = "postgresql+pg8000://{db_user}:{db_password}@/{db_name}?unix_sock=/cloudsql/{cloud_sql_connection_name}/.s.PGSQL.5432".format(
      db_user=db_user,
      db_password=db_pass,
      db_name=db_name,
      cloud_sql_connection_name=cloud_sql_connection_name
  )
  
