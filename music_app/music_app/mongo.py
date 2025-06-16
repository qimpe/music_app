import pymongo
import pymongo.errors
from django.conf import settings


class MongoClientManager:
    def __enter__(self) -> pymongo.MongoClient:
        self.connection = pymongo.MongoClient(
            host=settings.MONGO_HOST,
            port=settings.MONGO_PORT,
        )
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.connection.close()
