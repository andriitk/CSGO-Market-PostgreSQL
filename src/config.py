from environs import Env

env = Env()
env.read_env()

DB_HOST = env.str("POSTGRES_HOST")
DB_PORT = env.str("POSTGRES_PORT")
DB_NAME = env.str("POSTGRES_DB")
DB_USER = env.str("POSTGRES_USER")
DB_PASS = env.str("POSTGRES_PASSWORD")

REDIS_PORT = env.str("REDIS_PORT")
REDIS_HOST = env.str("REDIS_HOST")
