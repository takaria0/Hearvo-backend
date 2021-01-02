import os
import datetime

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
import bcrypt

import Hearvo.config as config
from ..app import logger
from ..models import db, User, UserSchema, UserInfo
from Hearvo.middlewares.detect_language import get_lang_id

#########################################
# Schema
#########################################
user_schema = UserSchema()
users_schema = UserSchema(many=True)

#########################################
# Routes to handle API
#########################################
class SignupResource(Resource):

  def post(self):
    lang_id = get_lang_id(request.base_url)
    user_name = request.json["user_name"].lower()
    email = request.json["email"].lower()
    password = request.json["password"]

    check_email = User.query.filter_by(email=email).first()
    check_user_name = UserInfo.query.filter_by(name=user_name).first()

    if (check_email is not None):
      res_obj =  {"message": "このメールアドレスは既に使われています"}
      status_code = 400
      return res_obj, status_code

    if (check_user_name is not None):
      res_obj =  {"message": "このユーザーネームは既に使われています"}
      status_code = 400
      return res_obj, status_code
        
    # generate hashed password using bcrypt.
    # for more info, look for the doc of bcrypt
    salt = bcrypt.gensalt(rounds=15, prefix=b'2a') # generate salt, 2^15 = 32768
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8") # hashed password

    try:
      new_user = User(
        email=email,
        hashed_password=hashed_password,
      )

      db.session.add(new_user)
      db.session.flush()

      new_user_info = UserInfo(
        name=user_name,
        user_id=new_user.id,
        lang_id=lang_id,
      )

      db.session.add(new_user_info)
      db.session.commit()

      res_obj = {"message": "アカウントを作成しました"}
      status_code = 200
      
    except:
      db.session.rollback()
      res_obj =  {"message": "アカウントの作成に失敗しました"}
      status_code = 400

    finally:
      pass
      # db.session.close()
    
    return res_obj, status_code


class LoginResource(Resource):

  def post(self):
    lang_id = get_lang_id(request.base_url)
    email = request.json["email"].lower()
    password = request.json["password"]

    current_user = User.query.filter_by(email=email).first()

    if not current_user:
      return {"message": "ログインに失敗しました"}, 401

    hashed_password = current_user.hashed_password

    # password matching
    if (bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))):

      user_info_obj = UserInfo.query.filter_by(
        user_id=current_user.id,
        lang_id=lang_id
      ).first()

      user_info_obj.login_count = user_info_obj.login_count + 1
      db.session.add(user_info_obj)
      db.session.commit()
      
      expires = datetime.timedelta(days=30)
      access_token = create_access_token(identity=str(user_info_obj.id), expires_delta=expires)
      # headers = {'Set-Cookie': access_token}
      return {"token": access_token}, 200 #, headers

    else:
      db.session.rollback()
      return {"message": "ログインに失敗しました"}, 401


    
class LogoutResource(Resource):
  @jwt_required
  def post(self):
    # current_user_id = request.session()

    # expire the session
    # request.session()
    return {"message": "Logout"}


    
    

    




