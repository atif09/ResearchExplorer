import os
from dotenv import load_dotenv

load_dotenv()

class Config():

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///research_explorer.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true'

    PAPERS_PER_PAGE = int(os.environ.get('PAPERS_PER_PAGE', 20))
    MAX_SEARCH_RESULTS = int(os.environ.get('MAX_SEARCH_RESULTS', 1000))
 
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'simple'
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    CACHE_KEY_PREFIX = 'research_explorer:'
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    ALLOWED_EXTENSIONS = {'csv', 'json', 'txt', 'xlsx'}
 
    EXPORT_FOLDER = os.environ.get('EXPORT_FOLDER') or 'exports'
    MAX_EXPORT_NODES = int(os.environ.get('MAX_EXPORT_NODES', 10000))
    EXPORT_FORMATS = ['json', 'csv', 'xml']

    BACKUP_FOLDER = os.environ.get('BACKUP_FOLDER') or 'backups'
    AUTO_BACKUP_ENABLED = os.environ.get('AUTO_BACKUP_ENABLED', 'False').lower() == 'true'
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))
    MAX_BACKUP_SIZE_MB = int(os.environ.get('MAX_BACKUP_SIZE_MB', 100))

    MAX_GRAPH_NODES = int(os.environ.get('MAX_GRAPH_NODES', 1000))
    MAX_SUBGRAPH_DEPTH = int(os.environ.get('MAX_SUBGRAPH_DEPTH', 3))
    DEFAULT_GRAPH_LAYOUT = 'force-directed'
  
    DEFAULT_YEARS_BACK = int(os.environ.get('DEFAULT_YEARS_BACK', 10))
    MIN_COLLABORATION_PAPERS = int(os.environ.get('MIN_COLLABORATION_PAPERS', 2))
    MIN_HOTSPOT_PAPERS = int(os.environ.get('MIN_HOTSPOT_PAPERS', 3))
    MIN_CITATIONS_FOR_INFLUENCE = int(os.environ.get('MIN_CITATIONS_FOR_INFLUENCE', 10))
 
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/1'
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT') or '1000 per hour'
    RATELIMIT_HEADERS_ENABLED = True

    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'logs/research_explorer.log'
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 10))

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    API_VERSION = '1.0'
    API_TITLE = 'Research Explorer API'
    API_DESCRIPTION = 'Comprehensive research paper analysis and visualization API'
    SWAGGER_UI_DOC_EXPANSION = 'list'

    SEARCH_RESULTS_PER_PAGE = int(os.environ.get('SEARCH_RESULTS_PER_PAGE', 20))
    MAX_SEARCH_TERMS = int(os.environ.get('MAX_SEARCH_TERMS', 10))
    ENABLE_FUZZY_SEARCH = os.environ.get('ENABLE_FUZZY_SEARCH', 'True').lower() == 'true'

    MAX_TITLE_LENGTH = 500
    MAX_ABSTRACT_LENGTH = 5000
    MAX_AUTHOR_NAME_LENGTH = 200
    MAX_KEYWORD_LENGTH = 100
    MIN_YEAR = 1900
    MAX_YEAR = 2030

    DATABASE_POOL_SIZE = int(os.environ.get('DATABASE_POOL_SIZE', 10))
    DATABASE_POOL_TIMEOUT = int(os.environ.get('DATABASE_POOL_TIMEOUT', 20))
    DATABASE_POOL_RECYCLE = int(os.environ.get('DATABASE_POOL_RECYCLE', 3600))

    DEFAULT_SAMPLE_AUTHORS = 12
    DEFAULT_SAMPLE_KEYWORDS = 16
    DEFAULT_SAMPLE_PAPERS = 8
    DEFAULT_SAMPLE_CITATIONS = 9
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""

        directories = [
            app.config['UPLOAD_FOLDER'],
            app.config['EXPORT_FOLDER'],
            app.config['BACKUP_FOLDER'],
            'logs'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

        import logging
        logging.basicConfig(
            level=getattr(logging, app.config['LOG_LEVEL']),
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True
    CACHE_TYPE = 'simple'

    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///research_explorer_dev.db'

    AUTO_BACKUP_ENABLED = True
    BACKUP_RETENTION_DAYS = 7

class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = False
    CACHE_TYPE = 'null'

    RATELIMIT_ENABLED = False

    MAX_SEARCH_RESULTS = 100
    MAX_GRAPH_NODES = 50
    PAPERS_PER_PAGE = 10

    AUTO_BACKUP_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://username:password@localhost/research_explorer'

    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PREFERRED_URL_SCHEME = 'https'

    LOG_LEVEL = 'WARNING'

    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DATABASE_POOL_SIZE', 20)),
        'pool_timeout': int(os.environ.get('DATABASE_POOL_TIMEOUT', 20)),
        'pool_recycle': int(os.environ.get('DATABASE_POOL_RECYCLE', 3600)),
        'max_overflow': int(os.environ.get('DATABASE_MAX_OVERFLOW', 30))
    }

    AUTO_BACKUP_ENABLED = True
    BACKUP_RETENTION_DAYS = 30
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        import logging
        from logging.handlers import RotatingFileHandler, SMTPHandler

        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Research Explorer startup')

class DockerConfig(ProductionConfig):
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        import logging
        from logging import StreamHandler
        
        stream_handler = StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}

def get_config():
    return config[os.getenv('FLASK_ENV', 'default')]