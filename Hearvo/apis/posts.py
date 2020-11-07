import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource, Api

import Hearvo.config as config
from ..app import api, app
from ..models import Post, PostSchema

PRE = config.URL_PREFIX


# b_app = Blueprint('posts', __name__)
# api = Api(b_app)

# init Schema
post_schema = PostSchema()
posts_schema = PostSchema(many=True)

#########################################
# Routes to handle API
#########################################
class PostListResource(Resource):
    def get(self):
        posts = Post.query.all()
        return posts_schema.dump(posts)

    # new
    def post(self):
        new_post = Post(
            title=request.json['title'],
            content=request.json['content']
        )
        db.session.add(new_post)
        db.session.commit()
        return post_schema.dump(new_post)

@app.route('/')
def hello_world():
    target = os.environ.get('TARGET', 'World')
    return {
      "message": 'Hello {}!\n'.format(target),
      "content": "Hi",
    }



api.add_resource(PostListResource, f'/{PRE}/posts')

