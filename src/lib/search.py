from flask import current_app
from elasticsearch_dsl.query import MultiMatch
from elasticsearch_dsl import SearchAsYouType, Document, connections


class TagsIndex(Document):
    name = SearchAsYouType(max_shingle_size=3)

    class Index:
        name = "tags"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}


class UsersIndex(Document):
    name = SearchAsYouType(max_shingle_size=3)
    username = SearchAsYouType(max_shingle_size=3)

    class Index:
        name = "users"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}


def add_to_index(doc, model):
    connections.create_connection(hosts=current_app.search_host, timeout=60)
    doc.init()

    if model.__tablename__ == 'users':
        for i in model.query:
            doc(_id=i.id, name=i.profile.name,
                username=i.profile.username).save()
    else:
        for i in model.query:
            doc(_id=i.id, name=i.name).save()

    doc._index.refresh()


def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, id=model.id)


def query_index(index, term):
    connections.create_connection(hosts=current_app.search_host, timeout=20)
    results = []

    try:
        s = index.search()
        s.query = MultiMatch(query=term, type="bool_prefix", fields=["*"])
        response = s.execute()
    except Exception as e:
        print(e)
        return None

    for res in response:
        results.append(res.meta.id)
    return results, len(response)
