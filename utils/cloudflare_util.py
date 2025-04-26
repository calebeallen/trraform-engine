
import boto3
import os
from dotenv import load_dotenv
from typing import Tuple, Dict
import botocore.exceptions


if os.getenv("ENV") != "prod":   
    load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("CF_R2_API_ENDPOINT"),
    aws_access_key_id=os.getenv("CF_R2_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("CF_R2_SECRET_KEY"),
    region_name="auto",
)

def get_item_r2(
    bucket: str, 
    key: str
) -> Tuple[bytes, Dict]:
    
    try:
        res = s3.get_object(Bucket=bucket, Key=key)
        return res["Body"].read(), res.get("Metadata", {})
    
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None, {}
        raise



def put_object(
    bucket: str, 
    key: str, 
    data: str, 
    content_type="application/octet-stream", 
    metadata=None
):
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
        Metadata=metadata or {}
    )
