import os
from collections import Counter
from datetime import datetime, timedelta, timezone, date


from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

import Hearvo.config as config
from ..app import logger, cache
from ..models import db, VoteSelect, VoteSelectSchema, VoteSelectUser, Post, UserInfoPostVoted, UserInfoSchema, UserInfo, VoteSelectUserSchema
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
    # vote_selects = VoteSelect.query.all()
    # return vote_selects_schema.dump(vote_selects)
    return {}, 200

  # @jwt_required
  # def post(self):
  #   new_vote_select = VoteSelect(
  #     post_id=request.json["post_id"],
  #     content=request.json['content'],
  #     created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
  #   )

  #   try:
  #     db.session.add(new_vote_select)
  #     db.session.commit()
  #     res_obj = {"message": "created"}
  #     status_code = 200
  #   except:
  #     db.session.rollback()
  #     res_obj = {"message": "created"}
  #     status_code = 400
  #   finally:
  #     pass
  #     # db.session.close()


  #   return res_obj, status_code

class CountVoteSelectResource(Resource):

  @jwt_required
  def post(self):
    logger_api("request.json", str(request.json))
    post_id = request.json["post_id"]

    post_obj = Post.query.filter_by(id=post_id).first() # DB access
    vote_selects_obj = post_obj.vote_selects # lazy loading

    vote_select_ids = [obj.id for obj in vote_selects_obj]

    """
    Below code may be super inefficient
    """
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
    user_info_id = get_jwt_identity()
    logger_api("user_info_id", user_info_id)
    vote_select_id = request.json["vote_select_id"]
    post_id = request.json["post_id"]
    logger_api("vote_select_id", vote_select_id)
    logger_api("post_id", post_id)
    new_vote_select = VoteSelectUser(
      vote_select_id=vote_select_id,
      user_info_id=user_info_id,
      post_id=post_id,
      created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
    )

    post_obj = Post.query.get(post_id)
    post_obj.num_vote = post_obj.num_vote + 1

    user_info_post_voted_obj = UserInfoPostVoted(
      user_info_id=user_info_id,
      post_id=post_id,
      vote_type_id=1,
      created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
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



class MultipleVoteUsersResource(Resource):

  @jwt_required
  def post(self):
    logger_api("request.json", request.json)

    user_info_id = get_jwt_identity()
    parent_id = request.json["parent_id"]
    result = request.json["result"]

    """
    check if the user has already voted for the post
    """
    check_obj = UserInfoPostVoted.query.filter_by(post_id=parent_id, user_info_id=user_info_id).all()
    check_list = [obj.user_info_id for obj in check_obj]
    if len(check_list) >= 1:
      res_obj = {"message": "failed to create"}
      status_code = 200
      logger.info("ALREADY CREATED")
      return res_obj, status_code
      
    """
    create assosiation between the user, the post and the vote result
    """
    new_vote_select_list = []
    user_info_post_voted_list = []
    for each in result:
      new_vote_select_list.append(
        VoteSelectUser(
          vote_select_id=each["vote_select_id"],
          user_info_id=user_info_id,
          post_id=each["post_id"],
          created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
        )
      )
      user_info_post_voted_list.append(
        UserInfoPostVoted(
          user_info_id=user_info_id,
          post_id=each["post_id"],
          vote_type_id=1, # important
          created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
        )
      )


    """
    update parent post's num of posts
    """
    post_obj = Post.query.get(parent_id)
    post_obj.num_vote = post_obj.num_vote + 1
    
    user_info_post_voted_list.append(
      UserInfoPostVoted(
        user_info_id=user_info_id,
        post_id=parent_id,
        vote_type_id=3, # important
        created_at=datetime.now(
            timezone(timedelta(hours=0), 'UTC')).isoformat()
      )
    )

    # try:
    db.session.bulk_save_objects(new_vote_select_list)
    db.session.bulk_save_objects(user_info_post_voted_list)
    db.session.add(post_obj)
    db.session.commit()

    res_obj = {"message": "created"}
    status_code = 200
    # except:
    #   db.session.rollback()
    #   res_obj = {"message": "failed to create"}
    #   status_code = 400

    return res_obj, status_code


def gender_num_to_text(gender, lang):

  if lang == "jp":
    jp_gender = {
      0: '男性',
      1: '女性',
      2: 'その他'
    }
    return jp_gender[gender]

  return

def slice_content_length(content):
  content = str(content)
  if len(content) > 12:
    content = content[0:12] + "...";
  
  return content


def get_first_result(first_target, parent_id):
  """
  first_target: post_id or gender or age

  return
  [
    {
      "content": "大学生",
      "user_info_id_list: [1,2,5,10]
    },
    {
      "content": "高校生",
      "user_info_id_list: [3,4,7]
    },
    {
      "content": "小学生",
      "user_info_id_list: [9,8]
    }
  ]
  """
  target_type = first_target["type"]

  user_info_schemas = UserInfoSchema(many=True)
  vote_select_user_schemas = VoteSelectUserSchema(many=True)

  result = []
  if target_type == "post_id":
    post_id = first_target["data"]
    vote_select_obj_list =  VoteSelect.query.filter_by(post_id=post_id).join(VoteSelectUser, VoteSelectUser.post_id == VoteSelect.post_id, isouter=True).all()

    for vote_select_obj in vote_select_obj_list:
      content = vote_select_obj.content
      content = slice_content_length(content)

      users = user_info_schemas.dump(vote_select_obj.users) # lazy loading
      user_info_id_list = [user["id"] for user in users]
      result.append({"content": content, "user_info_id_list": user_info_id_list})
    

  if target_type == "gender":
    gender_list = [0, 1, 2]
    vote_select_user_obj =  VoteSelectUser.query.filter_by(post_id=parent_id).all()
    vote_select_user_obj = vote_select_user_schemas.dump(vote_select_user_obj)
    

    for gender in gender_list:
      user_info_id_list = [vote_obj["user_info_id"] for vote_obj in vote_select_user_obj if vote_obj["user_info"]["gender"] == gender]
      result.append({"content": gender_num_to_text(gender, 'jp'), "user_info_id_list": user_info_id_list}) # f"debug": vote_select_user_obj})


  if target_type == "age":
    current = datetime.now(timezone(timedelta(hours=0), 'UTC')).year
    vote_select_user_obj =  VoteSelectUser.query.filter_by(post_id=parent_id).all()
    vote_select_user_obj = vote_select_user_schemas.dump(vote_select_user_obj)
    
    # age 0 to 9
    user_info_id_list_0_9 =  [vote_obj["user_info_id"] for vote_obj in vote_select_user_obj 
    if (current - 9 <= vote_obj["user_info"]["birth_year"] and vote_obj["user_info"]["birth_year"] <= current) ]
    result.append({"content": '0-9', "user_info_id_list": user_info_id_list_0_9}) 
    # age 10 to 19
    user_info_id_list_10_19 =  [vote_obj["user_info_id"] for vote_obj in vote_select_user_obj 
    if (current - 19 <= vote_obj["user_info"]["birth_year"] and vote_obj["user_info"]["birth_year"] <= current - 10) ]
    result.append({"content": '10-19', "user_info_id_list": user_info_id_list_10_19}) 
    # age 20 to 29
    user_info_id_list_20_29 =  [vote_obj["user_info_id"] for vote_obj in vote_select_user_obj 
    if (current - 29 <= vote_obj["user_info"]["birth_year"] and vote_obj["user_info"]["birth_year"] <= current - 20) ]
    result.append({"content": '20-29', "user_info_id_list": user_info_id_list_20_29})
    # age 30 to 39
    user_info_id_list_30_39 =  [vote_obj["user_info_id"] for vote_obj in vote_select_user_obj 
    if (current - 39 <= vote_obj["user_info"]["birth_year"] and vote_obj["user_info"]["birth_year"] <= current - 30) ]
    result.append({"content": '30-39', "user_info_id_list": user_info_id_list_30_39})
    # age 40 to 49
    user_info_id_list_40_49 =  [vote_obj["user_info_id"] for vote_obj in vote_select_user_obj 
    if (current - 49 <= vote_obj["user_info"]["birth_year"] and vote_obj["user_info"]["birth_year"] <= current - 40) ]
    result.append({"content": '40-49', "user_info_id_list": user_info_id_list_40_49})
    # age 50 to 59
    user_info_id_list_50_59 =  [vote_obj["user_info_id"] for vote_obj in vote_select_user_obj 
    if (current - 59 <= vote_obj["user_info"]["birth_year"] and vote_obj["user_info"]["birth_year"] <= current - 50) ]
    result.append({"content": '50-59', "user_info_id_list": user_info_id_list_50_59})
    # age 60 to 69
    user_info_id_list_60_69 =  [vote_obj["user_info_id"] for vote_obj in vote_select_user_obj 
    if (current - 69 <= vote_obj["user_info"]["birth_year"] and vote_obj["user_info"]["birth_year"] <= current - 60) ]
    result.append({"content": '60-69', "user_info_id_list": user_info_id_list_60_69})
    # age 70 to 79
    user_info_id_list_70_79 =  [vote_obj["user_info_id"] for vote_obj in vote_select_user_obj 
    if (current - 79 <= vote_obj["user_info"]["birth_year"] and vote_obj["user_info"]["birth_year"] <= current - 70) ]
    result.append({"content": '70-79', "user_info_id_list": user_info_id_list_70_79})
    # age 80 to 89
    user_info_id_list_80_89 =  [vote_obj["user_info_id"] for vote_obj in vote_select_user_obj 
    if (current - 89 <= vote_obj["user_info"]["birth_year"] and vote_obj["user_info"]["birth_year"] <= current - 80) ]
    result.append({"content": '80-89', "user_info_id_list": user_info_id_list_80_89})
    # age 90 to 99
    user_info_id_list_90_99 =  [vote_obj["user_info_id"] for vote_obj in vote_select_user_obj 
    if (current - 99 <= vote_obj["user_info"]["birth_year"] and vote_obj["user_info"]["birth_year"] <= current - 90) ]
    result.append({"content": '90-99', "user_info_id_list": user_info_id_list_90_99})
    # age 100 to 109
    user_info_id_list_100_109 =  [vote_obj["user_info_id"] for vote_obj in vote_select_user_obj 
    if (current - 109 <= vote_obj["user_info"]["birth_year"] and vote_obj["user_info"]["birth_year"] <= current - 100) ]
    result.append({"content": '100-109', "user_info_id_list": user_info_id_list_100_109})
    # age 110 to 119
    user_info_id_list_110_119 =  [vote_obj["user_info_id"] for vote_obj in vote_select_user_obj 
    if (current - 119 <= vote_obj["user_info"]["birth_year"] and vote_obj["user_info"]["birth_year"] <= current - 110) ]
    result.append({"content": '110-119', "user_info_id_list": user_info_id_list_110_119})

  return result


def get_second_result(first_result, second_target):
  """
  return 

  [
    {
      "content": "大学生",
      "アンドロイド": 10,
      "iPhone": 5,
      "その他"：10
    },
    {
      "content": "高校生",
      "アンドロイド": 8,
      "iPhone": 2,
      "その他"：15
    }
  ]
  """

  target_type = second_target["type"]
  user_info_schemas = UserInfoSchema(many=True)

  result = []
  if target_type == "post_id":
    post_id = second_target["data"]

    for first in first_result:
      first_content = first["content"]
      user_info_id_list = first["user_info_id_list"]
      vote_select_obj_list =  VoteSelect.query.filter_by(post_id=post_id).join(VoteSelectUser, VoteSelectUser.post_id == VoteSelect.post_id, isouter=True).filter(VoteSelectUser.user_info_id.in_(user_info_id_list)).all()

      append_content = {"content": first_content}

      """
      if vote was 0
      """
      if len(vote_select_obj_list) == 0:
        vote_select_obj_list = VoteSelect.query.filter_by(post_id=post_id).all()
        for vote_select_obj in vote_select_obj_list:
          content = vote_select_obj.content
          """ only number string cause error in nivo bar charts. so add underscore to it """
          try:
            int_content = int(content)
            content = str(content) + "_" 
          except:
            pass
          content = slice_content_length(content)
          append_content[content] = 0

      else:
        """
        if you insert the same content, this won't work.
        """
        for vote_select_obj in vote_select_obj_list:
          content = vote_select_obj.content
          users = vote_select_obj.users
          users = user_info_schemas.dump(users) # filtering
          users = [user for user in users if user["id"] in user_info_id_list]
          """ only number string cause error in nivo bar charts. so add underscore to it """
          try:
            int_content = int(content)
            content = str(content) + "_" 
          except:
            pass
          content = slice_content_length(content)
          append_content[content] = len(users) # here, the same content cannot save in the same place
          # append_content[f'debug_{content}'] = user_info_schemas.dump(users)

      result.append(append_content)

  if target_type == "gender":

    for first in first_result:
      first_content = first["content"]
      user_info_id_list = first["user_info_id_list"]
      append_content = {"content": first_content}

      male = UserInfo.query.filter(UserInfo.gender==0, UserInfo.id.in_(user_info_id_list)).all()
      female = UserInfo.query.filter(UserInfo.gender==1, UserInfo.id.in_(user_info_id_list)).all()
      other = UserInfo.query.filter(UserInfo.gender==2, UserInfo.id.in_(user_info_id_list)).all()
      append_content[gender_num_to_text(0, 'jp')] = len(male)
      append_content[gender_num_to_text(1, 'jp')] = len(female)
      append_content[gender_num_to_text(2, 'jp')] = len(other)

      result.append(append_content)

  if target_type == "age":

    for first in first_result:
      first_content = first["content"]
      user_info_id_list = first["user_info_id_list"]
      append_content = {"content": first_content}

      current = datetime.now(timezone(timedelta(hours=0), 'UTC')).year

      users_0_9 = UserInfo.query.filter(current - 9 <= UserInfo.birth_year, UserInfo.birth_year <= current, UserInfo.id.in_(user_info_id_list)).all()
      users_10_19 = UserInfo.query.filter(current - 19 <= UserInfo.birth_year, UserInfo.birth_year <= current - 10, UserInfo.id.in_(user_info_id_list)).all()
      users_20_29 = UserInfo.query.filter(current - 29 <= UserInfo.birth_year, UserInfo.birth_year <= current - 20, UserInfo.id.in_(user_info_id_list)).all()
      users_30_39 = UserInfo.query.filter(current - 39 <= UserInfo.birth_year, UserInfo.birth_year <= current - 30, UserInfo.id.in_(user_info_id_list)).all()
      users_40_49 = UserInfo.query.filter(current - 49 <= UserInfo.birth_year, UserInfo.birth_year <= current - 40, UserInfo.id.in_(user_info_id_list)).all()
      users_50_59 = UserInfo.query.filter(current - 59 <= UserInfo.birth_year, UserInfo.birth_year <= current - 50, UserInfo.id.in_(user_info_id_list)).all()
      users_60_69 = UserInfo.query.filter(current - 69 <= UserInfo.birth_year, UserInfo.birth_year <= current - 60, UserInfo.id.in_(user_info_id_list)).all()
      users_70_79 = UserInfo.query.filter(current - 79 <= UserInfo.birth_year, UserInfo.birth_year <= current - 70, UserInfo.id.in_(user_info_id_list)).all()
      users_80_89 = UserInfo.query.filter(current - 89 <= UserInfo.birth_year, UserInfo.birth_year <= current - 80, UserInfo.id.in_(user_info_id_list)).all()
      users_90_99 = UserInfo.query.filter(current - 99 <= UserInfo.birth_year, UserInfo.birth_year <= current - 90, UserInfo.id.in_(user_info_id_list)).all()
      users_100_109 = UserInfo.query.filter(current - 109 <= UserInfo.birth_year, UserInfo.birth_year <= current - 100, UserInfo.id.in_(user_info_id_list)).all()
      users_110_119 = UserInfo.query.filter(current - 119 <= UserInfo.birth_year, UserInfo.birth_year <= current - 110, UserInfo.id.in_(user_info_id_list)).all()

      append_content["0_9"] = len(users_0_9)
      append_content["10_19"] = len(users_10_19)
      append_content["20_29"] = len(users_20_29)
      append_content["30_39"] = len(users_30_39)
      append_content["40_49"] = len(users_40_49)
      append_content["50_59"] = len(users_50_59)
      append_content["60_69"] = len(users_60_69)
      append_content["70_79"] = len(users_70_79)
      append_content["80_89"] = len(users_80_89)
      append_content["90_99"] = len(users_90_99)
      append_content["100_109"] = len(users_100_109)
      append_content["110_119"] = len(users_110_119)
      result.append(append_content)


  return result



class VoteSelectCompareResource(Resource):

  # @jwt_required
  def post(self):
    """
    input 
    {
      "parent_id": 10,
      "first_target": {
        "type": "post_id",
        "data": 2
      },
      "second_target": {
        "type": "gender",
        "data": 0
      }
    }

    parent_id is used when first_target is gender or age, or both targets are age and gender.
    it's just a post id.

    when both targets are post_id, parent_id won't be used
    """
    logger_api("request.json", request.json)

    parent_id = request.json["parent_id"]
    first_target = request.json["first_target"]
    second_target = request.json["second_target"]

    if first_target["type"] == "gender" and second_target["type"] == "gender":
      return {"message": "Invalid data"}, 400

    if first_target["type"] == "age" and second_target["type"] == "age":
      return {"message": "Invalid data"}, 400

    """
    both target are post id
    """
    first_result = get_first_result(first_target, parent_id)
    second_result = get_second_result(first_result, second_target)


    return { "result" : second_result }, 200
