import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional, verify_jwt_in_request_optional
from datetime import datetime, timedelta, timezone

import Hearvo.config as config
from ..app import logger
from ..models import db, Comment, CommentSchema, VoteSelect
from .logger_api import logger_api
# from ..config import JST

#########################################
# Schema
#########################################
comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)

#########################################
# Routes to handle API
#########################################
class CommentResource(Resource):

  def get(self):
    try:
      verify_jwt_in_request_optional()
      user_info_id = get_jwt_identity()
    except:
      user_info_id = None

    if len(request.args) == 0:
      comments = Comment.query.all()
      status_code = 200
      return comments_schema.dump(comments), status_code

    elif "post_id" in request.args.keys():
      logger_api("request.args", str(request.args))
      logger_api("request.args[post_id]", str(request.args["post_id"]))
      post_id = request.args["post_id"]
      comments = Comment.query.filter_by(post_id=post_id).all()
      status_code = 200
      return comments_schema.dump(comments), status_code

    else:
      status_code = 400
      return [], status_code

    
  @jwt_required
  def post(self):
    logger_api("request.json", str(request.json))
    user_info_id = get_jwt_identity()
    post_id = request.json["post_id"]
    parent_id = request.json["parent_id"]

    if (parent_id == 0) or (parent_id == "0"):
      parent_id = None

    content = request.json["content"]

    new_comment = Comment(
      user_info_id=user_info_id,
      post_id=post_id,
      parent_id=parent_id,
      content=content,
      created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
    )

    logger_api("new_comment", str(new_comment))
    try:
      db.session.add(new_comment)
      db.session.commit()
      status_code = 200
    except:
      db.session.rollback()
      status_code = 400
    finally:
      pass
      # db.session.close()

    return comment_schema.dump(new_comment)




