import os
from collections import Counter
from datetime import datetime, timedelta, timezone, date


from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

import Hearvo.config as config
from ..app import logger, cache
from ..models import db, VoteSelect, VoteSelectSchema, VoteSelectUser, Post, UserInfoPostVoted
from .logger_api import logger_api
from Hearvo.utils import cache_delete_latest_posts, cache_delete_all_posts

#########################################
# Schema
#########################################
vote_select_schema = VoteSelectSchema()
vote_selects_schema = VoteSelectSchema(many=True)

#########################################
# Routes to handle API
#########################################
class VoteSelectResource(Resource):

  @jwt_required
  def get(self):
    vote_selects = VoteSelect.query.all()
    return vote_selects_schema.dump(vote_selects)

  @jwt_required
  def post(self):
    new_vote_select = VoteSelect(
      post_id=request.json["post_id"],
      content=request.json['content']
    )

    try:
      db.session.add(new_vote_select)
      db.session.commit()
      res_obj = {"message": "created"}
      status_code = 200
    except:
      db.session.rollback()
      res_obj = {"message": "created"}
      status_code = 400
    finally:
      pass
      # db.session.close()


    return res_obj, status_code

class CountVoteSelectResource(Resource):

  @jwt_required
  def post(self):
    logger_api("request.json", str(request.json))
    post_id = request.json["post_id"]
    post_obj = Post.query.filter_by(id=post_id).first()
    vote_selects_obj = post_obj.vote_selects

    vote_select_ids = [obj.id for obj in vote_selects_obj]
    vote_select_user_obj = VoteSelectUser.query.filter(VoteSelectUser.vote_select_id.in_(vote_select_ids)).all()
    count_obj = {obj.user_info_id: obj.vote_select_id for obj in vote_select_user_obj}
    id_content_table = {obj.id: obj.content for obj in vote_selects_obj}

    vote_selects_count = Counter(count_obj.values())
    total_vote = sum(vote_selects_count.values())
    data = dict(Counter(count_obj.values()))
    vote_selects_count = [{"vote_select_id": id, "count": data[id], "content": id_content_table[id]} if id in data.keys() else {"vote_select_id": id, "count": 0, "content": id_content_table[id]} for id in vote_select_ids ]


    res_obj = {"message": "count the vote", "vote_select_ids": vote_select_ids, "vote_selects_count": vote_selects_count, "total_vote": total_vote}
    status_code = 200
    return res_obj, status_code



class VoteSelectUserResource(Resource):
  
  @jwt_required
  def get(self):
    user_info_id = get_jwt_identity()
    post_id = request.args["post_id"]
    vote_selects = VoteSelectUser.query.filter_by(user_info_id=user_info_id, post_id=post_id).all()
    vote_selects_list = [obj.user_info_id for obj in vote_selects]

    post_obj = Post.query.get(post_id)
    end_at = str(post_obj.end_at)

    try:
      end_date = datetime.fromisoformat(end_at)
      today = datetime.now(timezone(timedelta(hours=0), 'UTC'))

      if end_date < today:
        end = True
      else:
        end = False

    except:
      end = False


    if len(vote_selects_list) >= 1:
      res_obj = {"voted": True, "end": end}
      status_code = 200
    else:
      res_obj = {"voted": False, "end": end}
      status_code = 200

    return res_obj, status_code

  @jwt_required
  def post(self):
    logger_api("request.json", request.json)
    cache_delete_all_posts()
    user_info_id = get_jwt_identity()
    logger_api("user_info_id", user_info_id)
    vote_select_id = request.json["vote_select_id"]
    post_id = request.json["post_id"]
    logger_api("vote_select_id", vote_select_id)
    logger_api("post_id", post_id)
    new_vote_select = VoteSelectUser(
      vote_select_id=vote_select_id,
      user_info_id=user_info_id,
      post_id=post_id
    )

    post_obj = Post.query.get(post_id)
    post_obj.num_vote = post_obj.num_vote + 1

    user_info_post_voted_obj = UserInfoPostVoted(
      user_info_id=user_info_id,
      post_id=post_id,
      vote_type_id=1,
    )

    check_obj = VoteSelectUser.query.filter_by(post_id=post_id, user_info_id=user_info_id).all()
    check_list = [obj.user_info_id for obj in check_obj]
    if len(check_list) >= 1:
      res_obj = {"message": "failed to create"}
      status_code = 200
      logger.info("ALREADY CREATED")
      return res_obj, 
      
    try:
      db.session.add(new_vote_select)
      db.session.add(post_obj)
      db.session.add(user_info_post_voted_obj)
      db.session.commit()

      

      res_obj = {"message": "created"}
      status_code = 200
    except:
      db.session.rollback()
      res_obj = {"message": "failed to create"}
      status_code = 400
    finally:
      pass


    return res_obj, status_code




