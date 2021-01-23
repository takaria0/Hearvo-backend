import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import bcrypt
from datetime import datetime, timedelta, timezone

import Hearvo.config as config
from ..app import logger
from ..models import db, User, UserGETSchema, UserInfo, UserInfoGETSchema,Group,UserInfoGroup
from Hearvo.middlewares.detect_language import get_lang_id
from .logger_api import logger_api



#########################################
# Schema
#########################################
# group_schema = UserInfoGETSchema()
# users_info_schema = UserInfoGETSchema(many=True)

#########################################
# Routes to handle API
#########################################
class GroupResource(Resource):
  @jwt_required
  def post(self):
    title = request.json["title"]
    user_info_id = get_jwt_identity()
    try:
        new_group = Group(
        user_info_id=user_info_id,
        title=title,
        created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
        )
        db.session.flush(new_group)
        group_id = new_group.id

        new_user_info_group = UserInfoGroup(
        user_info_id=user_info_id,
        group_id=group_id,
        created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
        )
        db.session.add(new_user_info_group)
        db.session.commit()
        status_code = 200
        return [], status_code
    except:
        status_code = 400
        db.session.rollback()
        return [], status_code

  


