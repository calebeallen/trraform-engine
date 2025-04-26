
from concurrent.futures import ThreadPoolExecutor
import redis
import os
import struct
from dotenv import load_dotenv
from utils.plot_id import PlotId
from utils.chunk_id import ChunkId
from utils.plot_data import PlotData
from utils.chunk import decode_chunk, encode_chunk
from utils import cloudflare_util
from utils import utils
from utils.constants import PLOT_COUNT, SAMPLE_PERCENTAGE
import numpy as np
from utils import color_library
from distutils.util import strtobool

if os.getenv("ENV") != "prod":
    load_dotenv()

MAIN_BUILD_SIZE = 115

plot_id_to_pos = {}

# get id to pos map
with open("./static/L2.dat", "rb") as file:

    bin = file.read()
    n = len(bin) // 4
    vals = list(struct.unpack(f'<{n}I', bin))

    for i in range(0, len(vals), 2):
        plot_id = i // 2 + 1
        pos_idx = vals[i + 1]
        plot_id_to_pos[plot_id] = utils.i2p(pos_idx, MAIN_BUILD_SIZE) # main build size 115


redis_cli = redis.Redis(
    host='redis-16216.c15.us-east-1-4.ec2.redns.redis-cloud.com',
    port=16216,
    username='default',
    password=os.getenv("REDIS_PASSWORD"),
    db=0,
)

# get plot ids that need update
plot_ids = [PlotId.from_hex(m.decode()) for m in redis_cli.smembers("needs_update:plot_ids")]
# redis_cli.delete("needs_update:plot_ids")
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

def update_chunk(data):

    try:

        chunk_id = data["chunk_id"]
        plot_ids = data["plot_ids"]

        # get chunk data
        chunk_bytes, _ = cloudflare_util.get_item_r2("chunks", f"{str(chunk_id)}.dat")
        chunk_decoded = decode_chunk(chunk_bytes)
        chunk = {}

        # decode individual plot data
        for id, encoded_plot in chunk_decoded.items():
            chunk[id] = PlotData.decode(encoded_plot) 

        # pull updated plot data
        for plot_id in plot_ids:
            plot_data_bytes, meta_data = cloudflare_util.get_item_r2("plots", f"{str(plot_id)}.dat")
            plot_data = PlotData.decode(plot_data_bytes)
            plot_data.verified = strtobool(meta_data.get("verified", "false"))

            chunk[plot_id.id] = plot_data

        if chunk_id.is_base:

            # create point cloud
            samples = []

            for id, plot_data in chunk.items():
                
                world_offset = np.array(plot_id_to_pos[id])
                build_size = plot_data.build_data[1]
                expanded = utils.expand(plot_data.build_data)      
                cols = np.asarray(expanded)

                # Boolean mask: keep voxels that are “solid” *and* randomly chosen
                mask = (cols > PLOT_COUNT) & (np.random.rand(cols.size) < SAMPLE_PERCENTAGE / 100)
                idxs = np.nonzero(mask)[0]           # indices of selected voxels

                if idxs.size:
                    xyz = utils.i2p_vec(idxs, build_size)
                    rgb = color_library.get_color_vec(cols[idxs])

                    build_vects = np.hstack([xyz, rgb])   

                    # covert vectors to world position
                    build_vects[:,:3] /= (MAIN_BUILD_SIZE * build_size)
                    build_vects[:,:3] += world_offset

                    samples.append(build_vects)

            #if for some reason samples is empty, don't add point clouds
            if samples:
            
                points = np.vstack(samples)

                # store points for next layer to update
                np.save(f"./point_clouds/{str(chunk_id)}", points)

                # flag next layer chunk for update
                parent_chunk_id = chunk_id.get_base_parent()
                redis_cli.sadd("needs_update:l1", str(parent_chunk_id))

        # re-encode plots
        for id, plot_data in chunk.items():
            chunk[id] = plot_data.encode()

        # push to cloudflare
        encoded_chunk = encode_chunk(chunk)
        cloudflare_util.put_object("chunk-test", str(chunk_id), encoded_chunk)

    except Exception as e:
        print(e)
    


with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(update_chunk, update_chunks.values())


    