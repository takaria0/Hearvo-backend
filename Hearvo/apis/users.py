import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import bcrypt

import Hearvo.config as config
from ..app import logger
from ..models import db, User, UserGETSchema, UserInfo, UserInfoGETSchema, UserInfoPostVoted, UserInfoTopic
from Hearvo.middlewares.detect_language import get_country_id
from .logger_api import logger_api

DELETED_USER_NAME = "<削除済み>" 
DELETED_USER_NAME_MAP = {
  1: "<削除済み>",
  2: "<Deleted>"
}

#########################################
# Schema
#########################################
user_info_schema = UserInfoGETSchema()
users_info_schema = UserInfoGETSchema(many=True)

#########################################
# Routes to handle API
#########################################
class UserResource(Resource):
  @jwt_required
  def get(self):
    user_info_id = get_jwt_identity()

    if "profile_detail" in request.args.keys():
      following_topics = UserInfoTopic.query.filter_by(user_info_id=user_info_id).all()
      num_of_votes = UserInfoPostVoted.query.filter_by(user_info_id=user_info_id).all()
      user = UserInfo.query.filter_by(id=user_info_id).first()
      user = user_info_schema.dump(user)
      return { **user, "num_of_following_topics": len(following_topics), "num_of_votes": len(num_of_votes) }, 200


    user = UserInfo.query.filter_by(id=user_info_id).first()
    return user_info_schema.dump(user), 200

  @jwt_required
  def put(self):
    user_info_id = get_jwt_identity()

    user_info_obj = UserInfo.query.get(user_info_id)

    if "login_count" in request.args.keys():
      login_count = request.args["login_count"]
      try:
        user_info_obj.login_count = int(login_count)
        db.session.add(user_info_obj)
        db.session.commit()
        return {}, 200
      except:
        db.session.rollback()
        return {}, 400

    elif "initial_setting" in request.args.keys():
      gender = request.json["gender"]
      birth_year = request.json["birth_year"]
      gender_detail = request.json["gender_detail"]
      # occupation = request.json["occupation"]

      # UPDATE USER
      user_info_obj.gender = gender
      user_info_obj.birth_year = birth_year
      user_info_obj.gender_detail = gender_detail
      # user_info_obj.occupation = occupation

      try:
        db.session.add(user_info_obj)
        db.session.commit()
        status_code = 200
        return user_info_schema.dump(user_info_obj), status_code
        
      except:
        db.session.rollback()
        status_code = 400
        return {}, status_code

    else:
      gender = request.json["gender"]
      birth_year = request.json["birth_year"]

      user_info_obj.gender = gender
      user_info_obj.birth_year = birth_year
      
      try:
        db.session.add(user_info_obj)
        db.session.commit()
        status_code = 200
        return user_info_schema.dump(user_info_obj), status_code
      except:
        db.session.rollback()
        status_code = 400
        return {}, status_code


  @jwt_required
  def delete(self):
    user_info_id = get_jwt_identity()
    country_id = get_country_id(request)
    confirm_password = request.headers['confirmPassword']
    logger_api('confirm_password',confirm_password)

    try:
      user_info = UserInfo.query.filter_by(id=user_info_id).first()
      logger_api('user_info',user_info)
      logger_api('user_info.user_id',user_info.user_id)
      user = User.query.filter_by(id=user_info.user_id).first()
      hashed_password = user.hashed_password
      logger_api('user.hashed_password',user.hashed_password)
      if (bcrypt.checkpw(confirm_password.encode("utf-8"), hashed_password.encode("utf-8"))):
        
        # UPDATE EMAIL TO NULL, NAME TO <deleted>
        user.deleted_email = user.email
        user.email = None
        user_info.name = DELETED_USER_NAME_MAP[country_id]

        db.session.add(user)
        db.session.add(user_info)
        db.session.commit()
        
        return {"message": "Successfully deleted the account"}, 200

      else:
        logger_api('password doesnt mathced', [])
        return {"message": "Account deletion failed"}, 400

    except:
      import traceback
      traceback.print_exc()
      db.session.rollback()
      
      return {"message": "Account deletion failed"}, 400
    




class UserPasswordResource(Resource):

  @jwt_required
  def put(self):
    user_info_id = get_jwt_identity()
    user_info_obj = UserInfo.query.get(user_info_id)

    old_password = request.json["old_password"]
    new_password = request.json["new_password"]

    # validate old password
    old_hashed_password = user_info_obj.hashed_password

    # password matching
    try:
      if (bcrypt.checkpw(old_password.encode("utf-8"), old_hashed_password.encode("utf-8"))):
        # matched
        # create new hashed password from new_password
        salt = bcrypt.gensalt(rounds=15, prefix=b'2a') # generate salt, 2^15 = 32768
        new_hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), salt).decode("utf-8") # hashed password

        user_info_obj.hashed_password = new_hashed_password        
        db.session.add(user_info_obj)
        db.session.commit()
        status_code = 200
        return {"message": "Password has changed"}, status_code
      else:
        status_code = 400
        return {}, status_code

    except:
      db.session.rollback()
      status_code = 400
      return {}, status_code


