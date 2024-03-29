import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource, Api

import Hearvo.config as config
from ..app import api, app
from .posts import PostResource
from .users import UserResource, UserPasswordResource, UserInfoFollowingResource
from .auth import SignupResource, LoginResource
from .vote_selects import VoteSelectResource, VoteSelectUserResource, CountVoteSelectResource, MultipleVoteUsersResource, VoteSelectCompareResource
from .vote_mjs import VoteMjResource, VoteMjUserResource, CountVoteMjResource
from .comments import CommentResource, CommentFavResource
from .groups import GroupResource, GroupUserInfoResource
from .topics import UserInfoTopicResource, TopicResource
from .reports import ReportResource
from .mlmodels.close_users import CloseUsersResource

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
api.add_resource(UserPasswordResource, f'/{PRE}/users/password')
api.add_resource(UserInfoFollowingResource, f'/{PRE}/users/followings')
api.add_resource(VoteSelectResource, f'/{PRE}/vote_selects')
api.add_resource(VoteSelectCompareResource, f'/{PRE}/vote_selects/compare')
api.add_resource(VoteMjResource, f'/{PRE}/vote_mjs')
api.add_resource(CountVoteMjResource, f'/{PRE}/count_vote_mjs')
api.add_resource(VoteMjUserResource, f'/{PRE}/vote_mj_users')
api.add_resource(VoteSelectUserResource, f'/{PRE}/vote_select_users')
api.add_resource(CountVoteSelectResource, f'/{PRE}/count_vote_selects')
api.add_resource(MultipleVoteUsersResource, f'/{PRE}/multiple_vote_users')
api.add_resource(CommentResource, f'/{PRE}/comments')
api.add_resource(CommentFavResource, f'/{PRE}/comments/fav')
api.add_resource(GroupResource, f'/{PRE}/groups')
api.add_resource(GroupUserInfoResource, f'/{PRE}/groups/users')
api.add_resource(TopicResource, f'/{PRE}/topics')
api.add_resource(UserInfoTopicResource, f'/{PRE}/topics/users')
api.add_resource(ReportResource, f'/{PRE}/reports')
api.add_resource(CloseUsersResource, f'/{PRE}/mlmodels/close_users')





