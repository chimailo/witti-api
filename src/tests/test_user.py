import json

from src import create_app
from src.config import TestingConfig
from src.blueprints.users.models import User


app = create_app(config=TestingConfig)


def test_follow(client, users, token):
    user = User.find_by_identity('regularuser')
    response = client.post(
        f'/api/users/follow/{user.id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert isinstance(data, list) is True


def test_unfollow(client, users, token):
    user = User.find_by_identity('commonuser')
    response = client.post(
        f'/api/users/unfollow/{user.id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert isinstance(data, list) is True


def test_get_followers(client, token):
    response = client.get(
        '/api/users/adminuser/followers/page/1',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert data.get('count') == 1
    assert data.get('hasNext') is False
    assert data.get('followers')[0]['username'] == 'commonuser'
    assert len(data.get('followers')) <= app.config['ITEMS_PER_PAGE']


def test_get_following(client, token):
    response = client.get(
        '/api/users/commonuser/following/page/1',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert data.get('count') == 1
    assert data.get('hasNext') is False
    assert data.get('following')[0]['username'] == 'adminuser'
    assert len(data.get('following')) <= app.config['ITEMS_PER_PAGE']


def test_get_user_posts(client, token, posts):
    response = client.get(
        '/api/users/adminuser/posts/page/1',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert data.get('hasNext') is False
    assert len(data.get('posts')) == 2
    assert len(data.get('posts')) <= app.config['ITEMS_PER_PAGE']


def test_get_user_comments(client, token, posts):
    response = client.get(
        '/api/users/adminuser/comments/page/1',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert data.get('hasNext') is False
    assert len(data.get('comments')) == 2
    assert len(data.get('comments')) <= app.config['ITEMS_PER_PAGE']


def test_get_user_likes(client, token, posts):
    response = client.get(
        '/api/users/adminuser/likes/page/1',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert data.get('hasNext') is False
    assert len(data.get('likes')) == 2
    assert len(data.get('likes')) <= app.config['ITEMS_PER_PAGE']
