from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, fields
from marshmallow_sqlalchemy.fields import Nested

from .models import Post, User, VoteSelect, VoteSelectUser, Comment, UserInfo, VoteType, VoteMj, MjOption, Topic, PostTopic, UserInfoTopic, Group

class GroupSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = Group
    include_relationships = True
    # exclude = ("hashed_password",)

class TopicSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = Topic
    include_relationships = True
    # exclude = ("hashed_password",)
    

class PostTopicSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = PostTopic
    include_relationships = True
    # exclude = ("hashed_password",)
    
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
    # exclude = ("vote_selects","posts","comments",)
  


class UserInfoSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = UserInfo
    include_relationships = True
    exclude = ("vote_selects","posts","comments",)
   

class VoteSelectSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = VoteSelect



class VoteSelectUserSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = VoteSelectUser



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



class CommentSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = Comment
    include_relationships = True

  user_info = Nested(UserInfoSchema(exclude=("vote_selects","posts","comments",)), many=False)
    # exclude = ("hashed_password",)


class PostSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = Post
    include_relationships = True
    # exclude = ("user",)

  vote_selects = Nested(VoteSelectSchema, many=True)
  vote_mjs = Nested(VoteMjSchema, many=True)
  topics = Nested(PostTopicSchema, many=True)
  mj_options = Nested(MjOptionSchema, many=True)
  user_info = Nested(UserInfoSchema(exclude=("vote_selects","posts","comments", )), many=False)
  vote_type = Nested(VoteTypeSchema(many=False))

  # comments = Nested(CommentSchema(exclude=("user",)), many=True)
    # fields = ("id", "title", "start_at", "end_at", "content", "created_at", "updated_at")
