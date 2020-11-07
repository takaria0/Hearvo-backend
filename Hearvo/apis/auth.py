import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource, Api
import bcrypt

import Hearvo.config as config
from ..app import api, app
from ..models import User, UserSchema

PRE = config.URL_PREFIX


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
      email = request.json["email"]
      password = request.json["password"]

      # generate hashed password using bcrypt.
      # for more info, look for the doc of bcrypt
      salt = bcrypt.gensalt(rounds=15, prefix=b'2a') # generate salt, 2^15 = 32768
      hashed_password = bcrypt.hashpw(password, salt) # hashed password
      

      new_user = User(
          hashed_password=hashed_password,
      )
      try:
        db.session.add(new_user)
        db.session.commit()
        return {"message": "Successfully created your account"}
      except:
        db.session.rollback()
        return {"message": "Couldn't create your account"}
      


class LoginResource(Resource):
    def post(self):
      email = request.json["email"]
      password = request.json["password"]

      current_user = User.query(email)
      hashed_password = current_user["hashed_password"]

      # if password matches
      if (bcrypt.checkpw(password, hashed_password)):
          request.session();
      else:
        return {"message": "Password doesn't match"}


    
class LogoutResource(Resource):
    def post(self):

      current_user_id = request.session()

      # expire the session
      request.session()
      return {"message": "Logout"}


    
    

    




api.add_resource(SignupResource, f'/{PRE}/signup')
api.add_resource(LoginResource, f'/{PRE}/login')

