import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

import Hearvo.config as config
from ..app import logger
from ..models import db, Post, PostSchema, VoteSelect
from .logger_api import logger_api

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
    posts = Post.query.join(Post.vote_selects).order_by(Post.id.desc()).all()
    status_code = 200
    return posts_schema.dump(posts), status_code

  @jwt_required
  def post(self):
    logger_api("request.json", str(request.json))
    user_id = get_jwt_identity()
    vote_selects = request.json["vote_selects"]
    vote_selects_list = [VoteSelect(content=obj["content"]) for obj in vote_selects]
    new_post = Post(
      user_id=user_id,
      title=request.json['title'],
      content=request.json['content'],
      vote_selects=vote_selects_list
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




