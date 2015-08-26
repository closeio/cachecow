import bson
import xxhash

from cachecow import CacheCow


class MongoCacheCow(CacheCow):
    """
    CacheCow for MongoEngine.

    Example usage:

    >>> class BlogPost(Document):
    >>>    title = StringField()

    >>> cache = MongoCache(initialized_redis_client)
    >>> bp = cache.get(BlogPost, 'title', 'First Title')  # fetches from Mongo (querying by { title: 'First Title' }) and caches it in Redis
    >>> bp = cache.get(BlogPost, 'title', 'First Title')  # fetches from Redis
    >>> cache.invalidate(BlogPost, 'title', 'First Title')  # invalidates the cache
    >>> bp = cache.get(BlogPost, 'title', 'First Title')  # fetches from Mongo (querying by { title: 'First Title' }) and caches it in Redis
    """

    def fetch(self, cls, id_field, id_val):
        return cls.objects.get(**{ id_field: id_val })

    def serialize(self, obj):
        return bson.json_util.dumps(obj._db_data)

    def deserialize(self, cls, cached_data):
        return cls._from_son(bson.json_util.loads(cached_data))

    def get_keys(self, cls, id_field, id_val):
        # store the data in redis under cache/flag:collection_name$id_field_name$id_value
        key = xxhash.xxh64(b'%s$%s$%s' % (cls._get_collection_name(), id_field, id_val)).hexdigest()
        return 'cache:' + key, 'flag:' + key

