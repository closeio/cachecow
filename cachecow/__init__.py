class CacheCow:
    """
    A simple class to cache individual objects in redis.

    It should be subclassed to handle a specific object type you want to
    cache. To store an object, CacheCow needs its retrieval class (i.e.
    a class you'll be able to use to retrieve the data from its primary
    storage), a field name the object can be identified by and a value of
    that field. For example, if you want to cache MongoEngine's documents,
    `cls` would be a Document class, `id_field` could be the 'id' field and
    `id_val` would correspond to the primary key of the doc you want to cache.
    """

    def __init__(self, redis):
        """Initialize CacheCow with a redis client."""

        self.redis = redis

        # Set up Redis scripts responsible for retrieval and caching of the data

        # Get the cached value. If we don't have a cached value, we try to set
        # the flag (which expires) and return the previous state of the flag.
        # cache_key should be supplied as KEYS[1], flag_key as KEYS[2]
        self.get_cached_or_set_flag = self.redis.register_script("""
            local cached = redis.call('get', KEYS[1])
            if cached then
                return { 0, cached }
            else
                local flag = redis.call('get', KEYS[2])
                if flag then
                    return { 1, nil }
                else
                    redis.call("setex", KEYS[2], 1, 60)
                    return { 0, nil }
                end
            end
        """)

        # If the flag wasn't previously set, then we set it and we cache the
        # JSON doc. We do this unless the cache got invalidated and the flag
        # was removed.
        # cache_key should be supplied as KEYS[1], flag_key as KEYS[2]
        # cached object's data should be supplied as ARGV[1]
        self.cache = self.redis.register_script("""
            local flag = redis.call('get', KEYS[2])
            -- If we don't have the flag then don't set the cache since it was invalidated.
            if flag then
                redis.call("set", KEYS[1], ARGV[1])
                redis.call("del", KEYS[2])
            end
        """)

    def get_keys(self, cls, id_field, id_val):
        """
        Get key names for the cache key (where the object's data is going to
        be stored), and the flag key (where the cache flag is going to be set).
        """
        raise NotImplementedError

    def get(self, cls, id_field, id_val):
        """
        Retrieve an object which `id_field` matches `id_val`. If it exists in
        the cache, it will be fetched from Redis. If not, it will be fetched
        via the `fetch` method and cached in Redis (unless the cache flag got
        invalidated in the meantime).
        """
        cache_key, flag_key = self.get_keys(cls, id_field, id_val)

        result = self.get_cached_or_set_flag(keys=(cache_key, flag_key))

        # in Lua, arrays cannot hold nil values, so e.g. if [1, nil] is returned,
        # we'll only get [1] here. That's why we need to append None ourselves.
        if len(result) == 1:
            result.append(None)

        previous_flag, cached_data = result

        # if cached data was found, deserialize and return it
        if cached_data is not None:
            deserialized = self.deserialize(cls, cached_data)

            # verify that the cached object matches our expectations
            # if not, return from the persistant storage instead.
            if self.verify(cls, id_field, id_val, deserialized):
                return deserialized
            else:
                # invalidate the cache if it didn't pass verification
                self.invalidate(cls, id_field, id_val)

        obj = self.fetch(cls, id_field, id_val)

        # If the flag wasn't previously set, then we set it and we're responsible
        # for putting the item in the cache. Do this unless the cache got
        # invalidated and the flag was removed.
        if not previous_flag:
            obj_serialized = self.serialize(obj)
            self.cache(keys=(cache_key, flag_key), args=(obj_serialized,))

        return obj

    def verify(self, cls, id_field, id_val, obj_from_cache):
        """
        Verify that the object we retrieved from cache matches the requested
        `id_field`/`id_val`.
        """
        return getattr(obj_from_cache, id_field) == id_val

    def serialize(self, obj):
        """Serialize the object before caching it."""
        raise NotImplementedError

    def deserialize(self, cls, cached_data):
        """Fetch the data that was retrieved from the cache."""
        raise NotImplementedError

    def fetch(self, cls, id_field, id_val):
        """Fetch the data from the original source."""
        raise NotImplementedError

    def invalidate(self, cls, id_field, id_val):
        """
        Invalidate the cache for a given Mongo object by deleting the cached
        data and the cache flag.
        """
        cache_key, flag_key = self.get_keys(cls, id_field, id_val)

        pipeline = self.redis.pipeline()
        pipeline.delete(cache_key)
        pipeline.delete(flag_key)
        pipeline.execute()

