from functools import lru_cache
<<<<<<< HEAD
from funboost import RedisMixin
=======
from funboost.utils.redis_manager import RedisMixin
>>>>>>> 1e74b5a0ff557f02c7b6d74e1ed00115bda6e0a0


class ProxyGetterConfig:
    PROXY_KEY_IN_REDIS_DEFAULT = 'proxy_free'
    REQUESTS_TIMEOUT = 5

@lru_cache()
def get_redis():
    return RedisMixin().redis_db_frame



