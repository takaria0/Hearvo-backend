import os
from collections import Counter
from datetime import datetime, timedelta, timezone, date


from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

import Hearvo.config as config
from ..app import logger
from ..models import db, VoteMj, VoteMjSchema, VoteMjUser, Post, UserInfoPostVoted, MjOption
from .logger_api import logger_api

#########################################
# Schema
#########################################
vote_select_schema = VoteMjSchema()
vote_selects_schema = VoteMjSchema(many=True)

#########################################
# Routes to handle API
#########################################
class VoteMjResource(Resource):

  @jwt_required
  def get(self):
    vote_selects = VoteMj.query.all()
    return vote_selects_schema.dump(vote_selects)

  @jwt_required
  def post(self):
    new_vote_select = VoteMj(
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

class CountVoteMjResource(Resource):

  @jwt_required
  def post(self):
    logger_api("request.json", str(request.json))
    post_id = request.json["post_id"]

    raw_mj_options = MjOption.query.filter_by(post_id=post_id).all()
    mj_options = [{"id":obj.id, "content":obj.content} for obj in raw_mj_options]

    dict_mj_options = {obj.id: obj.content for obj in raw_mj_options}
    # ADD USER FILTERING LATER
    vote_mj_user_obj = VoteMjUser.query.filter_by(post_id=post_id).join(VoteMj, VoteMj.id==VoteMjUser.vote_mj_id).all() 
    vote_mj_ids = list({obj.vote_mj_id for obj in vote_mj_user_obj})

    vote_mj_obj = [{"vote_mj_id": obj.id, "content": obj.content} for obj in VoteMj.query.filter(VoteMj.id.in_(vote_mj_ids)).all()]
    count_obj = [  {"vote_mj_id": mj_id, "mj_option_ids":[ obj.mj_option_id for obj in vote_mj_user_obj if mj_id==obj.vote_mj_id]} for mj_id in vote_mj_ids ]
    total_vote = len(count_obj[0]["mj_option_ids"]) if len(count_obj) != 0 else 0
    vote_mj_count = [{"count": [{"mj_option_id":key, "content":dict_mj_options[key], "count": val} for key, val in dict(Counter(obj["mj_option_ids"])).items()], "vote_mj_id": obj["vote_mj_id"]}  for obj in count_obj]

    res_obj = {"message": "count the vote", "vote_mj_ids": vote_mj_ids, "vote_mj_count": vote_mj_count, "total_vote": total_vote, "vote_mj_obj":vote_mj_obj, "mj_options": mj_options}
    status_code = 200
    return res_obj, status_code



class VoteMjUserResource(Resource):
  
  @jwt_required
  def get(self):
    user_info_id = get_jwt_identity()
    post_id = request.args["post_id"]
    vote_mjs = VoteMjUser.query.filter_by(user_info_id=user_info_id, post_id=post_id).all()
    vote_mjs_list = [obj.user_info_id for obj in vote_mjs]

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


    if len(vote_mjs_list) >= 1:
      res_obj = {"voted": True, "end": end}
      status_code = 200
    else:
      res_obj = {"voted": False, "end": end}
      status_code = 200

    return res_obj, status_code

  @jwt_required
  def post(self):
    logger_api("request.json", request.json)
    user_info_id = get_jwt_identity()
    vote_mj_obj = request.json["vote_mj_obj"]
    post_id = request.json["post_id"]
    new_vote_mj_list = [VoteMjUser(
      mj_option_id=obj["mj_option_id"],
      vote_mj_id=obj["vote_mj_id"],
      user_info_id=user_info_id,
      post_id=post_id) for obj in vote_mj_obj]

    post_obj = Post.query.get(post_id)
    post_obj.num_vote = post_obj.num_vote + 1
    logger_api("post_id", post_id)
    user_info_post_voted_obj = UserInfoPostVoted(
      user_info_id=user_info_id,
      post_id=post_id,
      vote_type_id=2,
    )
    logger_api("1", 1)
    check_obj = VoteMjUser.query.filter_by(post_id=post_id, user_info_id=user_info_id).all()
    check_list = [obj.user_info_id for obj in check_obj]
    logger_api("2", 2)
    logger_api("check_list", check_list)
    if len(check_list) >= 1:
      res_obj = {"message": "failed to create"}
      status_code = 200
      logger.info("ALREADY CREATED")
      return res_obj, status_code
    logger_api("aaaaaa", check_list)
    try:
      db.session.bulk_save_objects(new_vote_mj_list)
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
      # db.session.close()


    return res_obj, status_code




