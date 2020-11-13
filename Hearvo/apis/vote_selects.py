import os
from collections import Counter

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

import Hearvo.config as config
from ..app import logger
from ..models import db, VoteSelect, VoteSelectSchema, VoteSelectUser, Post

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
    post_id = request.json["post_id"]
    post_obj = Post.query.filter_by(id=post_id).first()
    vote_selects_obj = post_obj.vote_selects

    vote_select_ids = [obj.id for obj in vote_selects_obj]
    vote_select_user_obj = VoteSelectUser.query.filter(VoteSelectUser.vote_select_id.in_(vote_select_ids))
    count_obj = {obj.user_id: obj.vote_select_id for obj in vote_select_user_obj}
    
    vote_selects_count = Counter(count_obj.values())
    total_vote = sum(vote_selects_count.values())
    data = dict(Counter(count_obj.values()))
    vote_selects_count = [{"vote_select_id": id, "count": data[id]} if id in data.keys() else {"vote_select_id": id, "count": 0} for id in vote_select_ids ]

    res_obj = {"message": "count the vote", "vote_select_ids": vote_select_ids, "vote_selects_count": vote_selects_count, "total_vote": total_vote}
    status_code = 200
    return res_obj, status_code



class VoteSelectUserResource(Resource):
  
  @jwt_required
  def get(self):
    vote_selects = VoteSelectUser.query.all()
    return {"message": "aaa"}

  @jwt_required
  def post(self):
    user_id = get_jwt_identity()
    new_vote_select = VoteSelectUser(
      vote_select_id=request.json["vote_select_id"],
      user_id=user_id
    )

    try:
      db.session.add(new_vote_select)
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




