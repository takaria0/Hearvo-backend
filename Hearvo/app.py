from datetime import datetime
import logging
import os

import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource  # new

import Hearvo.config as config

logger = logging.getLogger()
app = Flask(__name__)
app.config["DEBUG"] = config.DEBUG_SETTING
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
api = Api(app)




