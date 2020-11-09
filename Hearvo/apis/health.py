import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource

import Hearvo.config as config
from ..app import app, logger
from ..models import Post, PostSchema


@app.route(f'/{PRE}/')
def hello_world():
    return {
      "message": 'health',
      "content": "Alive",
    }
