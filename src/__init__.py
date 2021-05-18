import logging
import os
from logging.handlers import SMTPHandler, RotatingFileHandler
# from elasticsearch import Elasticsearch
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from src.config import Config


# set up extensions
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()


def create_app(config=Config):
    """
    Create a Flask application using the app factory pattern.

    :return - object: Flask app
    """
    # Instantiate app
    app = Flask(__name__)

    # Set configuration
    app.config.from_object(config)

    # set up extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    # app.elasticsearch = Elasticsearch(app.config['ELASTICSEARCH_URL']) \
    #     if app.config['ELASTICSEARCH_URL'] else None
    # app.search_host = app.config['ES_HOST'] if app.config['ES_HOST'] else None
    # app.search_port = app.config['ES_PORT'] if app.config['ES_PORT'] else None

    @app.route('/api/ping')
    def ping():
        return {"message": "Ping!"}

    # Register Blueprint
    from src.blueprints.errors import errors
    from src.blueprints.search import search
    from src.blueprints.profiles.routes import profile
    from src.blueprints.tags.routes import tags
    from src.blueprints.posts.routes import posts
    from src.blueprints.users.routes import users
    from src.blueprints.messages.routes import messages

    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(tags)
    app.register_blueprint(profile)
    app.register_blueprint(search)
    app.register_blueprint(errors)
    app.register_blueprint(messages)

    from src.blueprints.users.models import User
    from src.blueprints.posts.models import Post
    from src.blueprints.tags.models import Tag
    from src.blueprints.profiles.models import Profile
    from src.blueprints.messages.models import Message, Chat, Notification

    @app.shell_context_processor
    def ctx():
        """shell context for flask cli """
        return {
            "app": app,
            "db": db,
            "User": User,
            "Profile": Profile,
            "Post": Post,
            "Tag": Tag,
            "Message": Message,
            "Chat": Chat,
            "Notification": Notification,
        }

    if not app.debug:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='Witti Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if not os.path.exists('logs'):
            os.mkdir('logs')
            file_handler = RotatingFileHandler(
                'logs/witti.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

            app.logger.setLevel(logging.INFO)
            app.logger.info('Witti startup')

    return app
