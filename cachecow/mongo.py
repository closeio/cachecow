import datetime
import decimal
import json
import xxhash

from bson import ObjectId, DBRef

from cachecow import CacheCow


class MongoEncoder(json.JSONEncoder):
    def default(self, value, **kwargs):
        if isinstance(value, ObjectId):
            return unicode(value)
        elif isinstance(value, DBRef):
            return value.id
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        if isinstance(value, datetime.date):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, decimal.Decimal):
            return str(value)
        return super(MongoEncoder, self).default(value, **kwargs)


class MongoCacheCow(CacheCow):
    """
    CacheCow for MongoEngine.

    Example usage:

    >>> class BlogPost(Document):
    >>>    title = StringField()

    >>> cache = MongoCache(initialized_redis_client)
    >>> bp = cache.get(BlogPost, 'title', 'First Title')  # fetches from Mongo (querying by { title: 'First Title' }) and caches it in Redis
    >>> bp = cache.get(BlogPost, 'title', 'First Title')  # fetches from Redis
    >>> cache.invalidate(bp.__class__, 'title', bp.title)
    >>> bp = cache.get(BlogPost, 'title', 'First Title')  # fetches from Mongo (querying by { title: 'First Title' }) and caches it in Redis
    """

    def fetch(self, cls, id_field, id_val):
        return cls.objects.get(**{ id_field: id_val })

    def serialize(self, obj):
        return json.dumps(obj._db_data, cls=MongoEncoder)

    def deserialize(self, cls, cached_data):
        return cls._from_son(json.loads(cached_data))

    def _get_keys(self, cls, id_field, id_val):
        """
        Get key names for the cache key (where the data is gonna be stored),
        and the flag key (where the cache flag is going to be set).
        """
        key = xxhash.xxh32(b'%s$%s$%s' % (cls._get_collection_name(), id_field, id_val)).hexdigest()
        return 'cache:' + key, 'flag:' + key

