
from concurrent.futures import ProcessPoolExecutor
import redis
import os
from dotenv import load_dotenv
from utils.plot_id import PlotId
from utils.chunk_id import ChunkId
from utils.constants import *
from update_chunks_worker import update_chunk
from utils import cloudflare_util

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

    # get plot ids that need update
    plot_ids = [PlotId.from_hex(m.decode()) for m in redis_cli.smembers("needs_update:plot_ids")]
    redis_cli.delete("needs_update:plot_ids")
    update_chunks = {}

    # group plot ids into their respective chunks
    for plot_id in plot_ids:

        chunk_id = ChunkId.from_plot_id(plot_id)
        chunk_id_str = str(chunk_id)

        if chunk_id_str not in update_chunks:
            update_chunks[chunk_id_str] = {
                "chunk_id": chunk_id,
                "plot_ids": []
            }

        update_chunks[chunk_id_str]["plot_ids"].append(plot_id)

    with ProcessPoolExecutor() as executor:
        executor.map(update_chunk, update_chunks.values())

    # purge cache
    urls = [f"{CHUNK_BUCKET_URL}/{cid}.dat" for cid in update_chunks]
    if urls:
        cloudflare_util.purge_cache_cdn(urls)

    