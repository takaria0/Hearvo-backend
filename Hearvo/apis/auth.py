import os
from datetime import datetime, timedelta, timezone
import re
import random
import string

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
import bcrypt
from google.oauth2 import id_token
from google.auth.transport import requests as g_requests


import Hearvo.config as config
from ..app import logger
from .logger_api import logger_api
from ..models import db, User, UserSchema, UserInfo
from Hearvo.middlewares.detect_language import get_country_id

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
    country_id = get_country_id(request)
    user_name = request.json["user_name"]
    email = request.json["email"].lower()
    password = request.json["password"]


    """
    Validate UserName, Email, Password
    """
    pattern = "^[A-Za-z0-9_-]*$" # Only contains alphabet, numbers, underscore, and dash
    if (len(user_name) > 20) or (not bool(re.match(pattern, user_name))):
      return {"message": "Invalid username"}, 400

    if (len(email)) > 350:
      return {"message": "Invalid email address"}, 400

    if (len(password) < 8) or (" " in password) or ("　" in password):
      return {"message": "Invalid password"}, 400


    check_email = User.query.filter_by(email=email).first()
    check_user_name = User.query.filter_by(name=user_name).first()

    if (check_email is not None):
      return {"message": "This email addres is already in use"}, 400

    if (check_user_name is not None):
      return {"message": "This username is already in use"}, 400
        
    # generate hashed password using bcrypt.
    # for more info, look for the doc of bcrypt
    salt = bcrypt.gensalt(rounds=15, prefix=b'2a') # generate salt, 2^15 = 32768
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8") # hashed password

    try:
      new_user = User(
        name=user_name,
        email=email,
        hashed_password=hashed_password,
        created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
      )

      db.session.add(new_user)
      db.session.flush()

      new_user_info = UserInfo(
        name=user_name,
        profile_name=user_name,
        user_id=new_user.id,
        country_id=country_id,
        created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
      )

      db.session.add(new_user_info)
      db.session.commit()

      res_obj = {"message": "Created a new account"}
      status_code = 200
      
    except:
      db.session.rollback()
      res_obj =  {"message": "Failed to create a new account"}
      status_code = 400

    finally:
      pass
      # db.session.close()
    
    return res_obj, status_code


class LoginResource(Resource):

  def post(self):
    country_id = get_country_id(request)

    """
    handles google login
    veryfiy the tokenId and look for the user by google_id

    if this is the first login, save google id, generate random user name and save user, user_info record. then return access token

    if this is the first login in another country, create a new user info record and return access token

    else, just simply return access token
    """
    if "google_login" in request.args.keys():
      token = request.headers["googleTokenId"]
      g_request = g_requests.Request()
      id_info = id_token.verify_oauth2_token(
          token, g_request, os.environ.get("GOOGLE_OAUTH_CLIENT_ID"))

      if id_info['iss'] != 'accounts.google.com':
          raise ValueError('Wrong issuer.')

      google_id = id_info['sub']
      gmail = id_info['email']

      current_user = User.query.filter_by(google_id=google_id).first()

      if current_user is None:  
        """
        genereate random user name
        at most three time to avoid duplicate 
        """
        count = 0
        for idx in range(3):
          lower_string = string.ascii_lowercase
          digits = string.digits
          generated_user_name = ''.join(random.choice(lower_string) for i in range(8)) + ''.join(random.choice(digits) for i in range(5))

          is_unique = User.query.filter_by(name=generated_user_name).first()

          if is_unique is None:
            break
          else:
            count += 1
            pass
        
        if count > 2:
          return {}, 400
        
        new_user = User(
          name=generated_user_name,
          google_id=google_id,
          google_email=gmail,
          created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
        )

        db.session.add(new_user)
        db.session.flush()

        new_user_info = UserInfo(
          name=generated_user_name,
          profile_name=generated_user_name,
          user_id=new_user.id,
          country_id=country_id,
          created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
        )

        db.session.add(new_user_info)
        db.session.flush()
        db.session.commit()
        expires = timedelta(days=60)
        access_token = create_access_token(identity=str(new_user_info.id), expires_delta=expires)
        return {"token": access_token}, 200

      else:
        user_info_obj = UserInfo.query.filter_by(
          user_id=current_user.id,
          country_id=country_id
        ).first()

        """
        login other countries
        create another user info obj using the same user name
        """
        if user_info_obj is None:
          another_country_user_info = UserInfo(
            user_id=current_user.id,
            country_id=country_id,
            name=current_user.name,
            profile_name=current_user.name,
            created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(),
            login_count=1
            )
          db.session.add(another_country_user_info)
          db.session.flush()
          user_info_id = another_country_user_info.id

        else:
          user_info_obj.login_count = user_info_obj.login_count + 1
          db.session.add(user_info_obj)
          user_info_id = user_info_obj.id

        db.session.commit()
        expires = timedelta(days=60)
        access_token = create_access_token(identity=str(user_info_id), expires_delta=expires)
        return {"token": access_token}, 200


    email = request.json["email"].lower()
    password = request.json["password"]

    current_user = User.query.filter_by(email=email).first()

    if not current_user:
      return {"message": "ログインに失敗しました"}, 401

    hashed_password = current_user.hashed_password

    # password matching
    if (bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))):
      logger_api("login_country_id", country_id)
      user_info_obj = UserInfo.query.filter_by(
        user_id=current_user.id,
        country_id=country_id
      ).first()

      """
      login other countries
      create another user info obj using the same user name
      """
      if user_info_obj is None:
        another_country_user_info = UserInfo(
          user_id=current_user.id,
          country_id=country_id,
          name=current_user.name,
          profile_name=current_user.name,
          created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(),
          login_count=1
          )
        db.session.add(another_country_user_info)
        db.session.flush()
        user_info_id = another_country_user_info.id

      else:
        user_info_obj.login_count = user_info_obj.login_count + 1
        db.session.add(user_info_obj)
        user_info_id = user_info_obj.id

      db.session.commit()
      expires = timedelta(days=60)
      access_token = create_access_token(identity=str(user_info_id), expires_delta=expires)
      return {"token": access_token}, 200

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


    
    

    



