import pytest

from src import create_app, db as _db
from src.config import TestingConfig
from src.tests.utils import add_user, add_post
from src.blueprints.users.models import User
from src.blueprints.posts.models import Post


@pytest.fixture(scope='session')
def app():
    """
    Create and configure a new app instance for each test.

    :returns -- object: Flask app
    """
    # create the app with test config.
    app = create_app(config=TestingConfig)

    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()


@pytest.fixture(scope='function')
def client(app):
    """
    Setup an app client, this gets executed for each client.

    :arguments: app {object} -- Pytext fixture
    :return: Flask app client
    """
    return app.test_client()


@pytest.fixture(scope='session')
def db(app):
    """
    Setup the database, this gets executed for every function

    :param app: Pytest fixture
    :return: SQLAlchemy database session
    """
    _db.drop_all()
    _db.create_all()
    _db.session.commit()

    add_user(name='admin', username='user', email='adminuser@test.com')

    return _db


@pytest.fixture(scope='function')
def session(db):
    """
    Allow very fast tests by using rollbacks and nested sessions.
    :param db: Pytest fixture
    :return: None
    """
    db.session.begin_nested()
    yield db.session
    db.session.rollback()

    return db


@pytest.fixture(scope='function')
def users(db, session):
    """
    Create user fixtures. They reset per test.

    :param db: Pytest fixture
    :return: SQLAlchemy database session
    """
    db.session.query(User).delete()

    admin = add_user(
        name='admin',
        username='adminuser',
        email='adminuser@test.com',
        bio='just about me.',
        is_admin=True
    )
    add_user(
        name='regular',
        username='regularuser',
        email='regularuser@test.com'
    )
    common = add_user(
        name='common',
        username='commonuser',
        email='commonuser@test.com'
    )

    common.follow(admin)

    return db


@pytest.fixture(scope='function')
def token(users):
    """
    Serialize a JWT token.

    :param db: Pytest fixture
    :return: JWT token
    """
    user = User.find_by_email('adminuser@test.com')
    return user.encode_auth_token()


@pytest.fixture(scope='function')
def posts(db, session, users):
    """
    Create posts fixtures. They reset per test.

    :param db: Pytest fixture
    :return: SQLAlchemy database session
    """
    db.session.query(Post).delete()

    u1 = User.find_by_email('adminuser@test.com')
    u2 = User.find_by_email('regularuser@test.com')
    u3 = User.find_by_email('commonuser@test.com')

    p1 = add_post(
        'Ut enim ad minim veniam, quis nostrud exercitation ', u1)
    p2 = add_post(
        'Ut enim ad minim veniam, quis nostrud exercitation ', u1)
    p3 = add_post(
        'Ut enim ad minim veniam, quis nostrud exercitation ', u3)

    add_post(
        'ullamco laboris nisi ut aliquip ex ea commodo consequat.', u1, p2.id)
    add_post(
        'ullamco laboris nisi ut aliquip ex ea commodo consequat.', u1, p1.id)
    add_post(
        'Ut enim ad minim veniam, quis nostrud exercitation ', u2, p1.id)
    add_post(
        'ullamco laboris nisi ut aliquip ex ea commodo consequat.', u3, p3.id)
    p1.likes.append(u1)
    p2.likes.append(u1)

    return db
