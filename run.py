import logging as logger
import os
from Hearvo.models import db  #import loaded Database 
from Hearvo.apis.routes import app # import loaded app
import Hearvo.config as config

if __name__ == "__main__":
  db.create_all() # create database defined as ./models
  logger.info('Hi, This Server is now running.') 
  app.run(debug=config.DEBUG_SETTING, host='0.0.0.0', port=config.APP_PORT)