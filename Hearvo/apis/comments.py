import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional, verify_jwt_in_request_optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_

import Hearvo.config as config
from ..app import logger
from ..models import db, Comment, CommentSchema, VoteSelect, CommentFav
from .logger_api import logger_api
# from ..config import JST

def update_num_of_good_or_bad(current_comment, good_or_bad, setting):
  """
  update number of good and bad of comment
  """
  # if fav already exists. need to balance the number
  if setting == "swap":
    if good_or_bad == 0:
      current_comment.num_of_bad = current_comment.num_of_bad + 1
      current_comment.num_of_good = current_comment.num_of_good - 1
    else:
      current_comment.num_of_bad = current_comment.num_of_bad - 1
      current_comment.num_of_good = current_comment.num_of_good + 1
    return current_comment

  # if create, add 1. if delete, subtract by 1
  num = 1 if setting == "addition" else -1
  if good_or_bad == 0:
    current_comment.num_of_bad = current_comment.num_of_bad + num
  else:
    current_comment.num_of_good = current_comment.num_of_good + num
  return current_comment

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
    """
    get comments of post

    post_id: id
    order_by: "popular" "latest"
    """
    order_by = request.args["order_by"] if "order_by" in request.args.keys() else ""

    try:
      verify_jwt_in_request_optional()
      user_info_id = get_jwt_identity()
    except:
      user_info_id = None

    if len(request.args) == 0:
      return {}, 200

    elif "post_id" in request.args.keys():
      logger_api("request.args", str(request.args))
      logger_api("request.args[post_id]", str(request.args["post_id"]))
      post_id = request.args["post_id"]

      # order by
      # TODO: add pagination
      if order_by == "popular":
        comments = Comment.query.filter_by(post_id=post_id).join(CommentFav, and_(Comment.id == CommentFav.comment_id,  CommentFav.user_info_id == user_info_id), isouter=True).order_by(Comment.num_of_good.desc()).limit(100).all()
      elif order_by == "latest":
        comments = Comment.query.filter_by(post_id=post_id).join(CommentFav, and_(Comment.id == CommentFav.comment_id, CommentFav.user_info_id == user_info_id), isouter=True).order_by(Comment.created_at.desc()).limit(100).all()
      else:
        comments = Comment.query.filter_by(post_id=post_id).join(CommentFav, and_(Comment.id == CommentFav.comment_id, CommentFav.user_info_id == user_info_id), isouter=True).order_by(Comment.created_at.desc()).limit(100).all()

      comment_list = comments_schema.dump(comments)

      """
      hide user info based on hide realname column
      """
      result = []
      for comment in comment_list:

        if comment["user_info"]["hide_realname"] == True:
          profile_name = comment["user_info"]["profile_name"]
          comment["user_info"] = {"name": comment["user_info"]["name"], "profile_name": profile_name}
          result.append(comment)
        else:
          profile_name = comment["user_info"]["first_name"] + " " + comment["user_info"]["middle_name"] + " " + comment["user_info"]["last_name"]
          comment["user_info"] = {"name": comment["user_info"]["name"], "profile_name": profile_name}
          result.append(comment)
      return result, 200

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

    if len(content) > 5000 or len(content) < 1:
      return {}, 400

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



class CommentFavResource(Resource):

  @jwt_required
  def post(self):
    """
    add fav to the comment

    comment_id: id
    good_or_bad: 1 is good, 0 is bad.
    """
    logger_api("request.json", str(request.json))
    user_info_id = get_jwt_identity()
    comment_id = request.json["comment_id"]
    good_or_bad = int(request.json["good_or_bad"])

    # Check if the comment exists
    current_comment = Comment.query.filter_by(id=comment_id).first()
    if current_comment is None:
      return {"message": "The comment doesn't exists"}, 400


    # Check if the user already favored
    comment_fav = CommentFav.query.filter_by(user_info_id=user_info_id, comment_id=comment_id).first()

    # New Fav
    if comment_fav is None:
      new_comment_fav = CommentFav(user_info_id=user_info_id, comment_id=comment_id, good_or_bad=good_or_bad)
      # update num of good or bad
      # current_comment = update_num_of_good_or_bad(current_comment, good_or_bad, "addition")
      if good_or_bad == 1:
        current_comment.num_of_good = current_comment.num_of_good + 1
      else:
        current_comment.num_of_bad = current_comment.num_of_bad + 1

    # Swap Fav
    elif comment_fav.good_or_bad != good_or_bad: # else update the current fav
      comment_fav.good_or_bad = good_or_bad
      new_comment_fav = comment_fav
      if good_or_bad == 1:
        current_comment.num_of_good = current_comment.num_of_good + 1
        current_comment.num_of_bad = current_comment.num_of_bad - 1
      else:
        current_comment.num_of_good = current_comment.num_of_good - 1
        current_comment.num_of_bad = current_comment.num_of_bad + 1
    
    else:
      return {"message": "Fav has't changed."}, 200


    try:
      db.session.add(new_comment_fav)
      db.session.add(current_comment)
      db.session.commit()
      status_code = 200
      return {"message": "Successfully created a fav."}, status_code
    except:
      db.session.rollback()
      status_code = 400
      return {"message": "Failed to create a fav."}, status_code


  @jwt_required
  def delete(self):
    """
    delete fav to the comment

    comment_id: id
    """
    logger_api("request.json", str(request.json))
    user_info_id = get_jwt_identity()
    comment_id = request.json["comment_id"]

    # Check if the fav exists
    comment_fav = CommentFav.query.filter_by(user_info_id=user_info_id, comment_id=comment_id).first()
    if comment_fav is None:
      status_code = 400
      return {"message": "The fav doesn't exist."}, status_code

    current_comment = Comment.query.filter_by(id=comment_id).first()
    # current_comment = update_num_of_good_or_bad(current_comment, comment_fav.good_or_bad, "subtract")
    if comment_fav.good_or_bad == 1:
      current_comment.num_of_good = current_comment.num_of_good - 1
    else:
      current_comment.num_of_bad = current_comment.num_of_bad - 1


    # delete fav from the database
    try:
      CommentFav.query.filter_by(user_info_id=user_info_id, comment_id=comment_id).delete()
      db.session.add(current_comment)
      db.session.commit()
      status_code = 200
      return {"message": "Successfully deleted the fav."}, status_code
    except:
      db.session.rollback()
      status_code = 400
      return {"message": "Failed to delete the fav."}, status_code

