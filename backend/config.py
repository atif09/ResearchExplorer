import os
from dotenv import load_dotenv

load_dotenv()

class Config():
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///research_trends.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    
    PAPERS_PER_PAGE = 20
    MAX_SEARCH_RESULTS = 1000
    
   
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    
 
    EXPORT_FOLDER = os.environ.get('EXPORT_FOLDER') or 'exports'
    MAX_EXPORT_NODES = 10000
    
    
    MAX_GRAPH_NODES = 1000
    MAX_SUBGRAPH_DEPTH = 3
    
 
    DEFAULT_YEARS_BACK = 10
    MIN_COLLABORATION_PAPERS = 2
    MIN_HOTSPOT_PAPERS = 3
    
 
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/1'
    RATELIMIT_DEFAULT = '1000 per hour'
    
   
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    CACHE_TYPE = 'simple'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    CACHE_TYPE = 'null'

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://username:password@localhost/research_trends'
    

    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}