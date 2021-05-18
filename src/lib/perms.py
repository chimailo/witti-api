import os
from sqlalchemy import exc

from src import db, create_app
# from src.blueprints.admin.models import Permission, Model

app = create_app(os.getenv('APP_SETTINGS'))


def set_model_perms(model, actions=[
        'add', 'delete', 'edit', 'view'], is_table=False):

    if is_table:
        name = str(model)
    else:
        name = f'{model.__name__}s'

    try:
        db.session.query(model)
    except exc.InvalidRequestError:
        return f"Error: {name} is not a valid sqlalchemy model or table."
    else:
        with app.app_context():
            try:
                mod = Model(name=name)
                mod.save()

                for action in actions:
                    perm = Permission(name=f'can {action} {name}')
                    perm.model_id = mod.id
                    perm.save()
            except (exc.IntegrityError, ValueError) as error:
                db.session.rollback()
                return f'Error: {error}'
