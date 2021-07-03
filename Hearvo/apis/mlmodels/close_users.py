import os
import hashlib
import json
from datetime import datetime, timedelta, timezone

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import bcrypt
import requests

import Hearvo.config as config
from ...app import logger
from ...utils import concat_realname
from ...models import db, User, UserGETSchema, UserInfo, UserInfoSchema,Group,UserInfoGroup, GroupSchema
from Hearvo.middlewares.detect_language import get_country_id
from ..logger_api import logger_api

#########################################
# Schema
#########################################
user_info_schema = UserInfoSchema(many=True)
# group_info_schema = GroupSchema()
# groups_info_schema = GroupSchema(many=True)

#########################################
# Routes to handle API
#########################################
class CloseUsersResource(Resource):

  @jwt_required
  def post(self):
    """
    add a new group
    """
    date = request.json["date"]
    user_info_id = request.json["user_info_id"]
    num_of_users = request.json["num_of_users"]
    country_id = get_country_id(request)
    current_datetime=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
    
    data = { 'user_info_id': user_info_id, 'date': date, 'num_of_users': num_of_users }
    res = requests.post('https://hearvo-ai-prod.herokuapp.com/api/v1/close_users', json=data).json()
    logger_api(res, "res")
    user_info_id_list = res["close_users"]
    
    if len(user_info_id_list) < 2:
      user_info_list = []
      return user_info_list, 400
    
    user_info_list = []
    for each_id in user_info_id_list:
      user_info = UserInfo.query.get(each_id)
      
      if user_info.hide_realname == False:
        profile_name = concat_realname(user_info.first_name, user_info.middle_name, user_info.last_name)
        name = user_info.name
        is_real_name = True
      else:
        profile_name = user_info.profile_name
        name = user_info.name
        is_real_name = False
        
      res_obj = {
        "id": user_info.id,
        "profile_name": profile_name,
        "name": name,
        "profile_img_url": user_info.profile_img_url
      }
      user_info_list.append(res_obj)
    
    
    return user_info_list, 200