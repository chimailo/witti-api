import os
import subprocess
import random
from datetime import datetime

import requests
import click
from sqlalchemy import exc, and_
from flask.cli import FlaskGroup

from src import create_app, db
from src.lib.search import add_to_index, TagsIndex, UsersIndex
from src.blueprints.users.models import User
from src.blueprints.posts.models import Post
from src.blueprints.profiles.models import Profile
from src.blueprints.tags.models import Tag
from src.blueprints.messages.models import Message, Chat, LastReadMessage

app = create_app()
cli = FlaskGroup(create_app=create_app)


def random_timestamp(start, end):
    return random.random() * (end - start) + start


@click.argument("path", default="src")
@cli.command()
def cov(path):
    """
    Run a test coverage report.

    :param path: Test coverage path
    :return: Subprocess call result
    """
    cmd = f"py.test --cov-report term-missing --cov {path}"
    return subprocess.call(cmd, shell=True)


@cli.command()
def routes():
    """
    List all of the available routes.

    :return: str
    """
    output = {}

    for rule in app.url_map.iter_rules():
        route = {
            'path': rule.rule,
            'methods': '({0})'.format(', '.join(rule.methods))
        }

        output[rule.endpoint] = route

    endpoint_padding = max(len(endpoint) for endpoint in output.keys()) + 2

    for key in sorted(output):
        click.echo('{0: >{1}}: {2}'.format(key, endpoint_padding, output[key]))


@cli.command()
def index_search_fields():
    """
    Index searchable fields.
    """
    add_to_index(TagsIndex, Tag)
    add_to_index(UsersIndex, User)


@cli.command()
@click.option(
    "--skip-init/--no-skip-init",
    default=True,
    help="Skip __init__.py files?"
)
@click.argument("path", default="src")
def flake8(skip_init, path):
    """
    Run flake8 to analyze your code base.

    :param skip_init: Skip checking __init__.py files
    :param path: Path to directory that flake8 would inspect
    :return: Subprocess call result
    """
    flake8_flag_exclude = ""

    if skip_init:
        flake8_flag_exclude = " --exclude __init__.py"

    cmd = f"flake8 {path}{flake8_flag_exclude} --ignore E128,E126,W504,F821"
    return subprocess.call(cmd, shell=True)


@cli.command()
@click.argument('path', default=os.path.join('src', 'tests'))
def test(path):
    """
    Run tests with Pytest.

    :param path: Test path
    :return: Subprocess call result
    """
    cmd = 'py.test {0}'.format(path)
    return subprocess.call(cmd, shell=True)


@click.argument("num_of_users", default=20)
@click.argument("num_of_posts", default=100)
@click.argument("num_of_comments", default=200)
@cli.command()
def seed_db(num_of_users, num_of_posts, num_of_comments):
    db_init()
    seed_users(num_of_users)
    seed_posts(num_of_posts)
    follow_tags()
    seed_comments(num_of_comments)
    seed_conversations()
    seed_messages()


# @cli.command()
def db_init():
    """Initialize the database."""
    db.drop_all()
    db.create_all()
    db.session.commit()
    print("Database was successfully initialized...")
    return None


# @cli.command()
def seed_users(num_of_users):
    """
    Seed the database with users.
    :param num_of_users: Number of users to seed the
    database with, default is 50.
    """
    print('Collecting users...')
    try:
        data = requests.get(
            'https://randomuser.me/api/?'
            f'results={num_of_users}'
            '&inc=name,email,login,picture,dob,location,nat'
        ).json()

        users = []

        for user in data.get('results'):
            u = User(email=user.get('email'))
            u.created_on = random_timestamp(
                datetime(2021, 3, 1), datetime(2021, 4, 28))

            u.profile = Profile()
            u.profile.username = user.get('login')['username']
            u.profile.name = user.get('name')['first'] + \
                ' ' + user.get('name')['last']
            u.profile.avatar = user.get('picture')['thumbnail']
            u.profile.dob = random_timestamp(
                datetime(1970, 3, 1), datetime(2002, 7, 28))
            u.profile.bio = f"Hi, I am {user.get('name')['first']} \
                from {user.get('location')['city']} \
                    {user.get('location')['state']}, {user.get('nat')}. \
                        I am a {user.get('dob')['age']} yrs old, who likes \
                            to tell jokes."
            u.profile.created_on = u.created_on
            users.append(u)

        print('Setting up followers/following...')

        for user in users:
            following = random.sample(
                users, k=random.randrange(5, int(len(users)/2)))
            user.followed.extend(following)

        print('Saving to database...')
        db.session.add_all(users)
        db.session.commit()

        print(f'Users table seeded with {num_of_users} users...')
    except exc.IntegrityError as error:
        db.session.rollback()
        print(f'Error: {error}')


# @cli.command()
def seed_posts(num_of_posts):
    """Seed the database with some posts."""
    users = User.query.all()
    posts1 = []
    posts2 = []
    post_objs = []
    tag_list = ['safe', 'broad', 'witty', 'humorous']

    print('Fetching posts...')

    for i in range(int(num_of_posts/15)):
        posts1.extend(requests.get(
            'https://official-joke-api.appspot.com/jokes/ten').json())

    for i in range(int(num_of_posts/15)):
        posts2.extend(requests.get(
            'https://sv443.net/jokeapi/v2/joke/Any?\
                blacklistFlags=nsfw,racist,sexist&type=twopart&amount=10',
            headers={'accept': 'application/json'}).json().get('jokes'))

    try:
        print('Saving posts to database...')
        for p in posts1:
            user = random.choice(users)

            tag = p.get('type')
            tags = [tag, random.choice(tag_list)]
            body = f"{p.get('setup')} - {p.get('punchline')}"

            post = Post()
            post.body = body
            post.user_id = user.id

            post.likes.extend(random.sample(users, k=random.randrange(36)))
            post.created_on = random_timestamp(
                datetime(2021, 5, 1), datetime(2021, 6, 28))

            for t in tags:
                tag = Tag.query.filter_by(name=t).first()

                if tag:
                    post.tags.append(tag)
                else:
                    tag = Tag(name=t)
                    db.session.add(tag)
                    post.tags.append(tag)

            post_objs.append(post)

        for p in posts2:
            user = random.choice(users)

            tag = p.get('category').lower()
            flags = p.get('flags')
            tags = [key.lower() for key in flags if flags[key] is True]
            tags.append(tag)
            if bool(p.get('safe')):
                tags.append('safe')

            body = f"{p.get('setup')} - {p.get('delivery')}"

            post = Post()
            post.body = body
            post.user_id = user.id
            post.created_on = random_timestamp(
                datetime(2021, 5, 1), datetime(2020, 6, 31))
            post.likes.extend(random.sample(users, k=random.randrange(30)))

            for t in tags:
                tag = Tag.query.filter_by(name=t).first()

                if tag:
                    post.tags.append(tag)
                else:
                    tag = Tag(name=t)
                    db.session.add(tag)
                    post.tags.append(tag)

            post_objs.append(post)

        db.session.add_all(post_objs)
        db.session.commit()

        print(f'Post table seeded with {num_of_posts} posts...')
    except Exception as error:
        print(f'Error: {error}')


# @cli.command()
def follow_tags():
    print('following tags...')
    tags = Tag.query.all()

    for user in User.query.all():
        user_tags = random.sample(tags, k=random.randrange(1, len(tags / 3)))
        user.tags.extend(user_tags)
        db.session.add(user)
    db.session.commit()


# @seed.command()
def seed_comments(num_of_comments):
    users = User.query.all()
    posts = Post.query.all()
    comments_list = []

    try:
        print('Fetching comments...')
        for i in range(int(num_of_comments/500)):
            comments_list.extend(requests.get(
                'https://jsonplaceholder.typicode.com/comments').json())

        comments = [comment.get('body') for comment in comments_list]

        comments_list = []

        for c in comments:
            user = random.choice(users)
            post = random.choice(posts)

            comment = Post(body=c)
            comment.user_id = user.id
            comment.comment_id = post.id
            comment.created_on = random_timestamp(
                datetime(2021, 7, 1), datetime(2021, 8, 21))
            comment.likes.extend(random.sample(users, k=random.randrange(12)))
            comments_list.append(comment)

        print('Saving to database...')
        db.session.add_all(comments_list)
        db.session.commit()

    except Exception as error:
        print(f'Error: {error}')


# @cli.command()
def seed_conversations():
    users = User.query.all()
    chats = []
    print('Setting up chats...')

    for user in users:
        sample = random.sample(
            user.followed.all(), k=(random.randrange(1, 5)))

        for u in sample:
            chat = Chat.query.filter(
                and_(Chat.user1_id == user.id, Chat.user2_id == u.id) |
                and_(Chat.user1_id == u.id, Chat.user2_id == user.id)).first()

            if chat:
                continue

            chat = Chat(user1_id=user.id, user2_id=u.id)
            chats.append(chat)
    print('Saving to database...')
    db.session.add_all(chats)
    db.session.commit()


# @cli.command()
def seed_messages():
    db.session.query(Message).delete()
    db.session.query(LastReadMessage).delete()
    chats = Chat.query.all()
    messages = []
    lr_msgs = []

    try:
        print('Fetching messages...')
        msgs = requests.get(
            'https://jsonplaceholder.typicode.com/todos').json()
    except Exception as error:
        print(f'Error: {error}')

    for c in chats:
        sample = random.sample(msgs, k=random.randrange(3, 8))

        for msg in sample:
            author = random.choice([c.user1_id, c.user2_id])
            message = Message(author_id=author, body=msg["title"])
            message.created_on = random_timestamp(
                datetime(2021, 1, 12), datetime(2021, 2, 11))
            message.chat_id = c.id
            messages.append(message)

            id = random.choice(
                [0, 0, 0, 0, c.user1_id, c.user2_id, 0, 0, 0, 0, 0, 0])

            if id != 0:
                user = User.find_by_id(id)
                user.deleted_messages.append(message)
                db.session.add(user)

            lrm = LastReadMessage.query.filter(
                and_(
                    LastReadMessage.user_id == author,
                    LastReadMessage.chat_id == c.id)
            ).first()

            if lrm:
                lrm.timestamp = random_timestamp(
                    datetime(2021, 1, 12), datetime(2021, 2, 1))
            else:
                lrm = LastReadMessage(user_id=author, chat_id=c.id)
                lrm.timestamp = random_timestamp(
                    datetime(2021, 1, 12), datetime(2021, 2, 1))
            lr_msgs.append(lrm)
            db.session.add(lrm)

    print('Saving to database...')
    db.session.add_all(messages)
    db.session.commit()


if __name__ == '__main__':
    cli()
