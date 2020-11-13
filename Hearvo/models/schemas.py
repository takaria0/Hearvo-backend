from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, fields
from marshmallow_sqlalchemy.fields import Nested

from .models import Post, User, VoteSelect, VoteSelectUser






class UserSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = User
    include_relationships = True
    exclude = ("hashed_password",)
    


class VoteSelectSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = VoteSelect



class VoteSelectUserSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = VoteSelectUser



class VoteMjSchema(SQLAlchemyAutoSchema):
  class Meta:
    pass



class MjOptionSchema(SQLAlchemyAutoSchema):
  class Meta:
    pass


class VoteMjUserSchema(SQLAlchemyAutoSchema):
  class Meta:
    pass


class PostSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = Post
    include_relationships = True
    exclude = ("user",)

  vote_selects = Nested(VoteSelectSchema, many=True)
    # fields = ("id", "title", "start_at", "end_at", "content", "created_at", "updated_at")
