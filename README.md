# CacheCow

Simple module for caching objects in Redis.

It provides a basic scaffolding class (`CacheCow`) you can use to build your own caching mechanism. It should work best with any database ORMs, though it's not limited to that use case.

### Why CacheCow?

* It's generic enough that you can easily extend it to work on top of any persistent storage.
* It abstracts out caching and cache invalidation for you.
* It ensures performance and consistency of your cache.

### How does CacheCow keep the data consistent?

CacheCow achieves consistency by using an additional key in Redis called a flag.
There are two atomic steps involved in the caching process.

1. Whenever you request an object that's not cached, we try to set the flag (which
expires). If the flag was set already, we don't cache any data. However, if it
wasn't set, we set it and proceed to step 2. Checking the flag and setting it
is atomic, meaning that it's guaranteed that only one operation will successfully
set it. Only the operation that succeeds is allowed to cache the object.
2. The second step of caching is to check the flag again and, only if it's still set,
cache the object. Then, the flag is cleared.

At any time, you can call the `invalidate` method and it will clear the cached data
as well as the related flag. It always results in a cleared cache, regardless of the timing:
* If you call `invalidate` before step 1, the cached data won't be found and it will be fetched from the persistent storage, and then cached.
* If you call `invalidate` between step 1 and 2, step 2 will recognize the flag is not set and it won't cache the data.
* If you call `invalidate` after step 2, cached data will be cleared after it was cached.

### Usage

What you need to do:

1. Decide what type of objects you want to cache (for the sake of this example, we'll decide to cache MongoEngine documents).
1. Subclass `CacheCow` and override methods for:
    * Generating unique Redis keys for each object (`get_keys`).
    * Fetching the objects (`fetch`) - for example, this can be a database lookup or a file read.
    * Serializing the objects into Redis (`serialize`).
    * Deserializing them after you retrieve them from the cache (`deserialize`).
1. Set up a `redis` client.
1. Initialize your `CacheCow` and use the `get` method to fetch and cache objects. You can also use `invalidate` to clear the cache.

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
        # store the data in redis under cache/flag:collection_name$id_field_name$id_value
        key = xxhash.xxh64(b'%s$%s$%s' % (cls._get_collection_name(), id_field, id_val)).hexdigest()
        return 'cache:' + key, 'flag:' + key
```

