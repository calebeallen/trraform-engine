from dotenv import load_dotenv
import os
import redis
import boto3
from utils.constants import *

load_dotenv()
redis_cli = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    username=REDIS_USERNAME,
    password=os.getenv("REDIS_PASSWORD"),
    db=REDIS_DB,
)

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("CF_R2_API_ENDPOINT"),
    aws_access_key_id=os.getenv("CF_R2_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("CF_R2_SECRET_KEY"),
    region_name="auto",
)


bucket_name = PLOTS_BUCKET_NAME
response = s3.list_objects_v2(Bucket=bucket_name)
ids = []

if 'Contents' in response:
    for obj in response['Contents']:
       ids.append(obj['Key'].split(".")[0])
else:
    print("Bucket is empty.")

redis_cli.sadd("needs_update:plot_ids", *ids)