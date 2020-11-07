import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource, Api

import Hearvo.config as config
from ..app import api, app
from ..models import db, Post, PostSchema

PRE = config.URL_PREFIX


#########################################
# Schema
#########################################
post_schema = PostSchema()
posts_schema = PostSchema(many=True)

#########################################
# Routes to handle API
#########################################
class PostResource(Resource):
    def get(self):
        posts = Post.query.all()
        return posts_schema.dump(posts)

    def post(self):
        new_post = Post(
            title=request.json['title'],
            content=request.json['content']
        )
        db.session.add(new_post)
        db.session.commit()
        return post_schema.dump(new_post)




api.add_resource(PostResource, f'/{PRE}/posts')

