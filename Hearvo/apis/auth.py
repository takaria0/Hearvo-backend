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
from ..models import db, User, UserSchema


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
    user_name = request.json["user_name"]
    email = request.json["email"]
    password = request.json["password"]

    # generate hashed password using bcrypt.
    # for more info, look for the doc of bcrypt
    salt = bcrypt.gensalt(rounds=15, prefix=b'2a') # generate salt, 2^15 = 32768
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8") # hashed password

    new_user = User(
      name=user_name,
      email=email,
      hashed_password=hashed_password,
    )

    try:
      db.session.add(new_user)
      db.session.commit()
      res_obj = {"message": "Successfully created your account"}
      status_code = 200
      
    except:
      db.session.rollback()
      res_obj =  {"message": "Couldn't create your account"}
      status_code = 400

    finally:
      pass
      # db.session.close()
    
    return res_obj, status_code


class LoginResource(Resource):

  def post(self):
    email = request.json["email"]
    password = request.json["password"]

    current_user = User.query.filter_by(email=email).first()

    if not current_user:
      return {"message": "Login failed"}, 400

    hashed_password = current_user.hashed_password

    # password matching
    if (bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))):
      expires = datetime.timedelta(days=30)
      access_token = create_access_token(identity=str(current_user.id), expires_delta=expires)
      return {"token": access_token, "user_id": current_user.id}, 200

    else:
      return {"message": "Login failed"}, 400


    
class LogoutResource(Resource):
  @jwt_required
  def post(self):
    # current_user_id = request.session()

    # expire the session
    # request.session()
    return {"message": "Logout"}


    
    

    




