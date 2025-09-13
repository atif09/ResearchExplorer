from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_caching import Cache
from flask_marshmallow import Marshmallow
from config import config
import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
ma = Marshmallow()

def create_app(config_name='development'):
  app = Flask(__name__)

  app.config.from_object(config[config_name])

  db.init_app(app)
  migrate.init_app(app,db)
  cache.init_app(app)
  ma.init_app(app)

  CORS(app, resources = {
    r'/api/*': {
      'origins': ['https://localhost:3000', 'http://127.0.0.1:3000'],
      'methods': ['GET','POST','PUT','DELETE','OPTIONS'],
      'allow_headers': ['Content-Type', 'Authorization'],
    }
  })

  from app.routes import bp as main_bp
  app.register_blueprint(main_bp, url_prefix='/api')

  from app.errors import bp  as errors_bp
  app.register_blueprint(errors_bp)

  if not app.debug and not app.testing: 
    if not os.path.exists('logs'):
      os.mkdir('logs')

    file_handler = RotatingFileHandler('logs/research_explorer.log',
                                        maxBytes=10240, backupCount=10)
    
    file_handler.setFormatter(logging.Formatter(
      '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Research Explorer startup')

  return app
