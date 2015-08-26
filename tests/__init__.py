import datetime
import mongoengine
import redis
import unittest

from mongoengine.context_managers import query_counter
from pymongo.read_preferences import ReadPreference

from cachecow.mongo import MongoCacheCow

class CacheCowTestCase(unittest.TestCase):

    def setUp(self):

        # Set up MongoEngine
        mongoengine.connect(
            db='cachecowtestdb',
            host='localhost',
            port=27017,
            read_preference=ReadPreference.PRIMARY,
        )

        # Set up Redis
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=9,
            socket_timeout=15
        )
        redis_client.flushdb() # clear the whole db

        # Set up MongoCacheCow
        self.mongo_cache = MongoCacheCow(redis_client)

        # Set up a sample MongoEngine document
        class BlogPost(mongoengine.Document):
            title = mongoengine.StringField()
            likes = mongoengine.IntField()
            date_created = mongoengine.DateTimeField()

            def summary(self):
                return '%s (%d likes)' % (self.title, self.likes)

            def save(self):
                if not self.date_created:
                    self.date_created = datetime.datetime.utcnow()
                super(BlogPost, self).save()

        self.BlogPost = BlogPost
        self.BlogPost.drop_collection()
        self.BlogPost.objects.create(title='First Title', likes=5)
        self.BlogPost.objects.create(title='Second Title', likes=10)

    def test_get_db_queries(self):
        """
        Make sure consecutive calls to mongo_cache.get don't hit the database
        for the same doc.
        """
        with query_counter() as q:
            for i in range(3):
                self.mongo_cache.get(self.BlogPost, 'title', 'First Title')

            self.mongo_cache.get(self.BlogPost, 'title', 'Second Title')

            # Only 2 queries to Mongo should be performed - one for caching
            # First Title and one for Second Title
            self.assertEqual(q, 2)

    def test_get_doc_consistency(self):
        """
        Make sure the doc fetched from Mongo doesn't differ from the cached
        doc fetched from Redis.
        """
        db_obj = self.mongo_cache.get(self.BlogPost, 'title', 'First Title')
        cached_obj = self.mongo_cache.get(self.BlogPost, 'title', 'First Title')

        self.assertEqual(db_obj.pk, cached_obj.pk)
        self.assertEqual(db_obj.title, cached_obj.title)
        self.assertEqual(db_obj.likes, cached_obj.likes)

        self.assertTrue(isinstance(db_obj.date_created, datetime.datetime))
        self.assertTrue(isinstance(cached_obj.date_created, datetime.datetime))
        self.assertEqual(db_obj.date_created, cached_obj.date_created.replace(tzinfo=None))  # bson parsing unfortunately includes the tz offset

        self.assertEqual(db_obj.summary(), cached_obj.summary())
        self.assertEqual(cached_obj.summary(), 'First Title (5 likes)')

    def test_invalidate(self):
        """Make sure simple cache invalidation works."""

        with query_counter() as q:
            self.mongo_cache.get(self.BlogPost, 'title', 'First Title')
            self.mongo_cache.invalidate(self.BlogPost, 'title', 'First Title')
            bp = self.mongo_cache.get(self.BlogPost, 'title', 'First Title')
            self.mongo_cache.invalidate(bp.__class__, 'title', bp.title)
            self.mongo_cache.get(self.BlogPost, 'title', 'First Title')
            self.assertEqual(q, 3)


if __name__ == '__main__':
    unittest.main()

