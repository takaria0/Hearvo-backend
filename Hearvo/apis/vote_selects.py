import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required

import Hearvo.config as config
from ..app import logger
from ..models import db, VoteSelect, VoteSelectSchema, VoteSelectUser


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


class VoteSelectUserResource(Resource):
  
  @jwt_required
  def get(self):
    vote_selects = VoteSelectUser.query.all()
    return {"message": "aaa"}

  @jwt_required
  def post(self):
    new_vote_select = VoteSelectUser(
      vote_select_id=request.json["vote_select_id"],
      user_id=request.json["user_id"]
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




