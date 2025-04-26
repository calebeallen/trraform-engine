from dotenv import load_dotenv
import os
import redis

if os.getenv("ENV") != "prod":
    load_dotenv()

redis_cli = redis.Redis(
    host='redis-16216.c15.us-east-1-4.ec2.redns.redis-cloud.com',
    port=16216,
    username='default',
    password=os.getenv("REDIS_PASSWORD"),
    db=0,
)

redis_cli.sadd("needs_update:plot_ids", "18")