import logging as logger
import os
from Hearvo.models import db  #import loaded Database 
from Hearvo.apis import app # import loaded app

if __name__ == "__main__":
  db.create_all() # create database defined as ./models
  logger.info('Hi, This Server is now running.') 
  app.run(debug=os.environ.get('DEBUG', True), host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))