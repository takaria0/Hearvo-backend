import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource, Api

import Hearvo.config as config
from ..app import api, app
from .posts import PostResource
from .users import UserResource
from .auth import SignupResource, LoginResource
from .vote_selects import VoteSelectResource, VoteSelectUserResource

PRE = config.URL_PREFIX


@app.route(f'/{PRE}/')
def hello_world():
    return {
      "message": 'health',
      "content": "Alive",
    }



api.add_resource(SignupResource, f'/{PRE}/signup')
api.add_resource(LoginResource, f'/{PRE}/login')
api.add_resource(PostResource, f'/{PRE}/posts')
api.add_resource(UserResource, f'/{PRE}/users')
api.add_resource(VoteSelectResource, f'/{PRE}/vote_selects')
api.add_resource(VoteSelectUserResource, f'/{PRE}/vote_select_users')


