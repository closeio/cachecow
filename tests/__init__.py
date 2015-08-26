import mongoengine
import redis
import unittest

from pymongo.read_preferences import ReadPreference

from cachecow.mongo import MongoCacheCow

class CacheCowTestCase(unittest.TestCase):

    def setUp(self):

        # Set up MongoEngine
        mongoengine.connect(
            db='cachecowtestdb',
            host='localhost',
            port=27017,
            read_preference=ReadPreference.PRIMARY
        )

        # Set up Redis
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=9,
            socket_timeout=15
        )

        # Set up MongoCacheCow
        self.mongo_cache = MongoCacheCow(redis_client)

    def test_get_db_queries(self):
        """
        Make sure consecutive calls to mongo_cache.get don't hit the database.
        """

        class BlogPost(mongoengine.Document):
            title = mongoengine.StringField()
            likes = mongoengine.IntField()

            def summary(self):
                return '%s (%d likes)' % (self.title, self.likes)

        BlogPost.drop_collection()
        BlogPost.objects.create(title='First Title', likes=5)
        BlogPost.objects.create(title='Second Title', likes=10)

        self.mongo_cache.get(BlogPost, 'title', 'First Title')


if __name__ == '__main__':
    unittest.main()

