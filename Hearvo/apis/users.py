import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

import Hearvo.config as config
from ..app import logger
from ..models import db, User, UserGETSchema


#########################################
# Schema
#########################################
user_schema = UserGETSchema()
users_schema = UserGETSchema(many=True)

#########################################
# Routes to handle API
#########################################
class UserResource(Resource):
  @jwt_required
  def get(self):
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    return user_schema.dump(user), 200

  @jwt_required
  def put(self):
    user_id = get_jwt_identity()
    user_obj = User.query.get(user_id)

    description = request.json["description"]
    gender = request.json["gender"]
    age = request.json["age"]
    occupation = request.json["occupation"]

    def update_user(user_obj, description, gender, age, occupation):
      user_obj.description = description
      user_obj.gender = gender
      user_obj.age = age
      user_obj.occupation = occupation
      return user_obj

    
    try:
      updated_user_obj = update_user(user_obj, description, gender, age, occupation)
      db.session.add(updated_user_obj)
      db.session.commit()
      status_code = 200
      return user_schema.dump(updated_user_obj), status_code
    except:
      db.session.rollback()
      status_code = 400
      return {}, status_code


    
    # return user_schema.dump(user), 200

  # @jwt_required
  # def post(self):
  #   # user_id = get_jwt_identity()
  #   new_post = User(
  #     user_id=request.json["user_id"],
  #     title=request.json['title'],
  #     content=request.json['content']
  #   )
  #   try:
  #     db.session.add(new_post)
  #     db.session.commit()
  #     status_code = 200
  #   except:
  #     db.session.rollback()
  #     status_code = 400
  #   finally:
  #     pass
  #     # db.session.close()

  #   return post_schema.dump(new_post)




