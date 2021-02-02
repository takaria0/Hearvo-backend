from datetime import datetime, timedelta, timezone
import logging
import os

import sqlalchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource  # new
from flask_migrate import Migrate  # 追加
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
from flask_cors import CORS
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address



import Hearvo.config as config


logging.basicConfig()
logger = logging.getLogger('sqlalchemy.engine')

if config.setting == "dev":
  # logger.setLevel(logging.DEBUG)
  logger.setLevel(logging.ERROR)
elif config.setting == "prod":
  logger.setLevel(logging.INFO)
    

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = config.SECRET_KET
app.config['JWT_TOKEN_LOCATION'] = ['headers']

# app.config['JWT_TOKEN_LOCATION'] = ['cookies']
# app.config['JWT_COOKIE_CSRF_PROTECT'] = True
# app.config['JWT_ACCESS_LIFESPAN'] = {'hours': 24}
# app.config['JWT_REFRESH_LIFESPAN'] = {'days': 30}

app.config["DEBUG"] = config.DEBUG_SETTING
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
cache = Cache()
cache.init_app(app, config=config.cache_config)
CORS(app, origins=config.ALLOW_ORIGIN_LIST, methods=["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"])
Migrate(app, db)
api = Api(app)
jwt = JWTManager(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    # default_limits=["3000 per day", "300 per hour"]
)



