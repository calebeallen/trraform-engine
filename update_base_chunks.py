
from concurrent.futures import ProcessPoolExecutor
import redis
import os
from utils.constants import *
from utils.chunk_id import ChunkId
from dotenv import load_dotenv
import sys
from update_base_chunks_worker import update_base_chunk 


if __name__ == "__main__":

    if os.getenv("ENV") != "prod":
        load_dotenv()

    redis_cli = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        username=REDIS_USERNAME,
        password=os.getenv("REDIS_PASSWORD"),
        db=REDIS_DB,
    )

    # get base chunks that need update
    layer = int(sys.argv[1])
    update_chunks = [ChunkId.from_string(m.decode()) for m in redis_cli.smembers(f"needs_update:l{layer}")]
    redis_cli.delete(f"needs_update:l{layer}")

    with ProcessPoolExecutor() as executor:
        executor.map(update_base_chunk, update_chunks)
