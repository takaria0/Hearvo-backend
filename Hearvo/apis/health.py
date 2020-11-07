import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource, Api

import Hearvo.config as config
from ..app import api, app
from ..models import Post, PostSchema

PRE = config.URL_PREFIX


@app.route('/')
def hello_world():
    return {
      "message": 'health',
      "content": "Alive",
    }
