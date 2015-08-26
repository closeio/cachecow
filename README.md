# cachecow
Simple module for caching objects in Redis.

It provides a basic scaffolding class (`CacheCow`) you can use to build your own caching mechanism. It should work best with any database ORMs, though it's not limited to that use case.

## Usage

What you need to do:

1. Decide what type of objects you want to cache (for the sake of this example, we'll decide to cache MongoEngine documents).
1. Subclass `CacheCow` and override methods for:
    * Generating unique Redis keys for each object (`get_keys`).
    * Fetching the objects (`fetch`) - for example, this can be a database lookup or a file read.
    * Serializing the objects into Redis (`serialize`).
    * Deserializing them after you retrieve them from the cache (`deserialize`).
1. Set up a `redis` client.
1. Initialize your `CacheCow` and use the `get` method to fetch and cache objects. You can also use `invalidate` to clear the cache. **`CacheCow` automatically prevents race conditions during cache invalidation.**

Here's an implementation of a simple MongoEngine document cache (available under `cachecow.mongo`), along with its usage:

```
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
        """
        Get key names for the cache key (where the data is gonna be stored),
        and the flag key (where the cache flag is going to be set).
        """
        key = xxhash.xxh64(b'%s$%s$%s' % (cls._get_collection_name(), id_field, id_val)).hexdigest()
        return 'cache:' + key, 'flag:' + key
```

