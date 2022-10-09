import redis


class RedisClient:
    def __init__(self):
        self.redis = redis.Redis(host="localhost", port=6379, db=0)
