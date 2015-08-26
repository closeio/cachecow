# cachecow
Simple module for caching objects in Redis.

It provides a basic scaffolding class (`CacheCow`) you can use to build your own caching mechanism. It should work best with any database ORMs, though it's not limited to that use case.

For an example, see `cachecow.mongo.MongoCacheCow` and the corresponsing tests that show how easy it is to implement MongoEngine document caching.

