import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required

import Hearvo.config as config
from ..app import logger
from ..models import db, Post, PostSchema


#########################################
# Schema
#########################################
post_schema = PostSchema()
posts_schema = PostSchema(many=True)

#########################################
# Routes to handle API
#########################################
class PostResource(Resource):
  @jwt_required
  def get(self):

    posts = Post.query.all()
    return posts_schema.dump(posts)

  @jwt_required
  def post(self):
    # user_id = get_jwt_identity()
    new_post = Post(
      user_id=request.json["user_id"],
      title=request.json['title'],
      content=request.json['content']
    )
    try:
      db.session.add(new_post)
      db.session.commit()
      status_code = 200
    except:
      db.session.rollback()
      status_code = 400
    finally:
      pass
      # db.session.close()

    return post_schema.dump(new_post)




