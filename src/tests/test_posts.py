import json

from src import create_app
from src.config import TestingConfig
from src.blueprints.posts.models import Post


app = create_app(config=TestingConfig)


def test_get_post(client, token, posts):
    post = Post.query.all()[0]
    response = client.get(
        f'/api/posts/{post.id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert isinstance(data, dict) is True


# def test_get_top_post(client, token):
#     response = client.get(
#         '/api/posts/top',
#         headers={'Authorization': f'Bearer {token}'}
#     )
#     data = json.loads(response.data.decode())
#     assert response.status_code == 200
#     assert data.get('hasNext') is False
#     assert len(data.get('posts')) == 2
#     assert len(data.get('posts')) <= app.config['ITEMS_PER_PAGE']


# def test_get_latest_post(client, token):
#     response = client.get(
#         '/api/posts/latest',
#         headers={'Authorization': f'Bearer {token}'}
#     )
#     data = json.loads(response.data.decode())
#     assert response.status_code == 200
#     assert data.get('hasNext') is False
#     assert len(data.get('posts')) == 2
#     assert len(data.get('posts')) <= app.config['ITEMS_PER_PAGE']


def test_create_post(client, token):
    response = client.post(
        '/api/posts',
        data=json.dumps({'post': 'ullamco laboris nisi ut aliquip ex ea'}),
        headers={'Authorization': f'Bearer {token}'},
        content_type='application/json',
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 201
    assert isinstance(data, dict) is True


def test_delete_post(client, token, posts):
    post = Post.query.all()[0]
    response = client.delete(
        f'/api/posts/{post.id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert isinstance(data, dict) is True


def test_delete_post_invalid(client, token, posts):
    post = Post.query.all()[-1]
    response = client.delete(
        f'/api/posts/{post.id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 401


def test_like_post(client, token, posts):
    post = Post.query.all()[-1]
    response = client.post(
        f'/api/posts/{post.id}/likes',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert isinstance(data, dict) is True


def test_unlike_post(client, token, posts):
    post = Post.query.all()[0]
    response = client.post(
        f'/api/posts/{post.id}/likes',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert isinstance(data, dict) is True


def test_get_comments(client, token, posts):
    post = Post.query.all()[0]
    response = client.get(
        f'/api/posts/{post.id}/comments/page/1',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert isinstance(data, dict) is True
    assert len(data.get('comments')) <= app.config['ITEMS_PER_PAGE']
    assert data.get('hasNext') is False


def test_create_comment(client, token, posts):
    post = Post.query.all()[0]
    response = client.post(
        f'/api/posts/{post.id}/comments',
        data=json.dumps({'comment': 'ullamco laboris nisi ut aliquip ex ea'}),
        headers={'Authorization': f'Bearer {token}'},
        content_type='application/json',
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 201
    assert data.get('body') == 'ullamco laboris nisi ut aliquip ex ea'


def test_update_comment(client, token, posts):
    post = Post.query.all()[1]
    comment = post.comments[0]
    response = client.put(
        f'/api/posts/{post.id}/comments/{comment.id}',
        data=json.dumps({'post': 'ullamco laboris nisi ut'}),
        headers={'Authorization': f'Bearer {token}'},
        content_type='application/json'
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert data.get('body') == 'ullamco laboris nisi ut'


def test_update_comment_invalid(client, token, posts):
    post = Post.query.all()[-1]
    comment = post.comments[-1]
    response = client.put(
        f'/api/posts/{post.id}/comments/{comment.id}',
        data=json.dumps({'post': 'ullamco laboris nisi ut'}),
        headers={'Authorization': f'Bearer {token}'},
        content_type='application/json'
    )
    assert response.status_code == 401


def test_delete_comment(client, token, posts):
    post = Post.query.all()[1]
    comment = post.comments[0]
    response = client.delete(
        f'/api/posts/{post.id}/comments/{comment.id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert isinstance(data, dict) is True


def test_delete_comment_invalid(client, token, posts):
    post = Post.query.all()[-1]
    comment = post.comments[-1]
    response = client.delete(
        f'/api/posts/{post.id}/comments/{comment.id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 401


def test_like_comment(client, token, posts):
    post = Post.query.all()[0]
    comment = post.comments[-1]
    response = client.post(
        f'/api/posts/{post.id}/comments/{comment.id}/likes',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(response.data.decode())
    assert response.status_code == 200
    assert isinstance(data, dict) is True
