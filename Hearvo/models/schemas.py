from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, fields
from marshmallow_sqlalchemy.fields import Nested

from .models import Post, User, VoteSelect, VoteSelectUser, Comment, UserInfo, VoteType, VoteMj, MjOption, Topic, PostTopic, UserInfoTopic, Group, UserInfoPostVoted, CommentFav

class GroupSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = Group
    include_relationships = True
    # exclude = ("hashed_password",)

class TopicSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = Topic
    include_relationships = True
    exclude = ("post_topic",)

  # post_topic_length = len(post_topic)
    

class PostTopicSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = PostTopic
    include_relationships = True
    exclude = ("created_at", "updated_at",)
    
  topic = Nested(TopicSchema, many=False)



class UserGETSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = User
    include_relationships = True
    exclude = ("hashed_password",)
    



class UserSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = User
    include_relationships = True
    exclude = ("hashed_password",)
    


class UserInfoGETSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = UserInfo
    include_relationships = True
    exclude = ("vote_selects","posts","comments","vote_select_user",)
  


class UserInfoSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = UserInfo
    include_relationships = True
    exclude = ("vote_selects","posts","comments","vote_select_user",)
   
class UserInfoPostVotedSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = UserInfoPostVoted
    include_relationships = True

  user_info = Nested(UserInfoSchema(exclude=("vote_selects","posts","comments","vote_select_user", )), many=True)


class VoteSelectUserSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = VoteSelectUser
    include_fk = True
    include_relationships = True

  user_info = Nested(UserInfoSchema(exclude=("vote_selects","posts","comments","vote_select_user", )), many=False)


class VoteSelectSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = VoteSelect
    include_relationships = True
    exclude = ("created_at", "updated_at",)

  users = Nested(UserInfoSchema(exclude=("vote_selects","posts","comments","vote_select_user", )), many=True)
  vote_select_users = Nested(VoteSelectUserSchema(many=True))


class VoteMjSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = VoteMj
    include_relationships = True
    exclude = ("post",)



class MjOptionSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = MjOption
    include_relationships = True
    exclude = ("post",)




class VoteMjUserSchema(SQLAlchemyAutoSchema):
  class Meta:
    pass

class VoteTypeSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = VoteType
    include_relationships = True
    exclude = ("posts",)

class CommentFavSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = CommentFav
    include_relationships = True
    include_fk = True

  

class CommentSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = Comment
    include_relationships = True

  user_info = Nested(UserInfoSchema(exclude=("vote_selects","posts","comments","vote_select_user",)), many=False)
  comment_favs = Nested(CommentFavSchema, many=True)
    # exclude = ("hashed_password",)


class PostSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = Post
    include_relationships = True
    # exclude = ("user",)

  vote_selects = Nested(VoteSelectSchema(exclude=("users",)), many=True)
  vote_mjs = Nested(VoteMjSchema, many=True)
  topics = Nested(PostTopicSchema, many=True)
  mj_options = Nested(MjOptionSchema, many=True)
  user_info = Nested(UserInfoSchema(exclude=("vote_selects","posts","comments", "vote_select_user",)), many=False)
  vote_type = Nested(VoteTypeSchema(many=False))
  

  # comments = Nested(CommentSchema(exclude=("user",)), many=True)
    # fields = ("id", "title", "start_at", "end_at", "content", "created_at", "updated_at")
