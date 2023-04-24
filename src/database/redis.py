import aioredis
import pickle
from config import REDIS_PORT, REDIS_HOST


# Func for add data to Redis DB
async def add_data_to_redis(table: str, data: dict | list, db: int):
    try:
        redis = await aioredis.from_url(url=f'redis://{REDIS_HOST}:{REDIS_PORT}/{db}')
        await redis.set(table, pickle.dumps(data))
        await redis.close()
    except Exception as ex:
        return f"Exception...{ex}"


# Func for get data from Redis DB
async def get_market_hash_names(table: str, db: int):
    redis = aioredis.from_url(url=f'redis://{REDIS_HOST}:{REDIS_PORT}/{db}')

    market_hash_names = await redis.get(table)
    if market_hash_names:
        market_hash_names = pickle.loads(market_hash_names)
        return market_hash_names
    return {}
