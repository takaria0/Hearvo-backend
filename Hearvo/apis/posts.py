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
    if "id" in request.args.keys():
      id = request.args["id"]
      post = Post.query.filter_by(id=id).join(Post.vote_selects).first()
      status_code = 200
      return post_schema.dump(post), status_code

    # TODO ADD num_comment, num_vote to Post table
    # elif "keyword" in request.args.keys():
    #   posts = Post.query.join(Post.vote_selects).order_by(Post.num_vote.desc()).all()
    #   status_code = 200


    else:
      posts = Post.query.join(Post.vote_selects).order_by(Post.id.desc()).all()
      status_code = 200
      return posts_schema.dump(posts), status_code

  @jwt_required
  def post(self):
    logger_api("request.json", str(request.json))
    user_id = get_jwt_identity()

    title = request.json['title']
    content = request.json['content']
    end_at = request.json['end_at']
    vote_selects = request.json["vote_selects"]
    vote_selects_list = [VoteSelect(content=obj["content"]) for obj in vote_selects]

    new_post = Post(
      user_id=user_id,
      title=title,
      content=content,
      end_at=end_at,
      vote_selects=vote_selects_list
    )
    try:
      db.session.add(new_post)
      db.session.commit()
      status_code = 200
      return post_schema.dump(new_post), status_code
    except:
      db.session.rollback()
      status_code = 400
      return {}, status_code
    finally:
      pass
      # db.session.close()

    




