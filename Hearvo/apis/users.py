import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

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
class UserResource(Resource):
  @jwt_required
  def get(self):
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    return user_schema.dump(user), 200

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




