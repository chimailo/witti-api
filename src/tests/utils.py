from src import db
from src.blueprints.profiles.models import Profile
from src.blueprints.users.models import User
from src.blueprints.posts.models import Post


def add_user(
        name,
        email,
        username='',
        avatar='',
        bio='',
        is_admin=False,):

    profile = Profile(name=name, bio=bio, username=username)
    profile.avatar = avatar or profile.set_avatar(email)

    user = User(password='password')
    user.email = email
    user.is_admin = is_admin
    user.profile = profile

    user.save()
    return user


def add_post(body, user, post_id=None):
    post = Post()
    post.body = body
    post.user_id = user.id

    if post_id:
        post.comment_id = post_id

    post_notifs = []
    for u in user.followers.all():
        post_notifs.append(user.add_notification(
            subject='post', item_id=post.id, id=u.id, post_id=post.id))

    db.session.add_all(post_notifs)
    post.save()
    return post
