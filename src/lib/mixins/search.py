from src import db
from src.lib.search import add_to_index, remove_from_index, \
    query_index, TagsIndex, UsersIndex


class SearchableMixin(object):
    @classmethod
    def search(cls, indexDoc, expression):
        ids, total = query_index(indexDoc, expression)

        if total == 0:
            return []

        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))

        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)).all()

    @classmethod
    def reindex(cls, doc):
        add_to_index(doc, cls)

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                if str(type(obj)) == 'User':
                    add_to_index(UsersIndex, obj)
                if str(type(obj)) == 'Tag':
                    add_to_index(TagsIndex, obj)

        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                if str(type(obj)) == 'User':
                    add_to_index(UsersIndex, obj)
                if str(type(obj)) == 'Tag':
                    add_to_index(TagsIndex, obj)

        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                if str(type(obj)) == 'User':
                    remove_from_index(UsersIndex, obj)
                if str(type(obj)) == 'Tag':
                    remove_from_index(TagsIndex, obj)
        session._changes = None


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)
