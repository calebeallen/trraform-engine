
import boto3
import os
from dotenv import load_dotenv
from typing import Tuple, Dict, List, Optional
import botocore.exceptions
import time
import requests
from .constants import *


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

def purge_cache_cdn(
    urls: List[str],
    batch_size: int = 100,
    max_urls_per_sec: int = 600,
    timeout: Optional[float] = None  # seconds, passed to requests
) -> None:

    pause = batch_size / max_urls_per_sec  # e.g. 100/600 ≈ 0.1667s

    api_url = f"https://api.cloudflare.com/client/v4/zones/{os.getenv('CF_ZONE_ID')}/purge_cache"
    headers = {
        "Authorization": f"Bearer {os.getenv('CF_API_TOKEN')}",
        "Content-Type":  "application/json",
    }

    for i in range(0, len(urls), batch_size):
        batch = urls[i : i + batch_size]
        payload = {
            "files": [
                {"url": u, "headers": {"Origin": ORIGIN}}
                for u in batch
            ]
        }

        resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"Error purging batch starting at index {i}: {e}\nResponse body: {resp.text}"
            )

        # throttle
        if i + batch_size < len(urls):
            time.sleep(pause)
