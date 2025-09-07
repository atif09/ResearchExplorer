from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from config import config

db = SQLAlchemy()
migrate=Migrate()

def create_app(config_name='development'):
  app = Flask(__name__)

  app.config.from_object(config[config_name])

  db.init_app(app)
  migrate.init_app(app,db)
  CORS(app)

  from app.routes import bp as main_bp
  app.register_blueprint(main_bp, url_prefix='/api')

  return app

