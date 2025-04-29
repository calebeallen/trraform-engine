
import redis
import os
import struct
from dotenv import load_dotenv
from utils.plot_id import PlotId
from utils.plot_data import PlotData
from utils.chunk import decode_chunk, encode_chunk
from utils import cloudflare_util
from utils import utils
from utils.constants import *
import numpy as np
from utils import color_library
from distutils.util import strtobool
import traceback

if os.getenv("ENV") != "prod":
    load_dotenv()

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
    host=REDIS_HOST,
    port=REDIS_PORT,
    username=REDIS_USERNAME,
    password=os.getenv("REDIS_PASSWORD"),
    db=REDIS_DB,
)

def update_chunk(data):

    try:

        chunk_id = data["chunk_id"]
        plot_ids = data["plot_ids"]

        # get chunk data
        chunk_bytes, _ = cloudflare_util.get_item_r2(CHUNKS_BUCKET_NAME, f"{str(chunk_id)}.dat")
        chunk_decoded = decode_chunk(chunk_bytes)
        chunk = {}

        # decode individual plot data
        for id, encoded_plot in chunk_decoded.items():
            chunk[id] = PlotData.decode(encoded_plot) 

        # pull updated plot data
        for plot_id in plot_ids:
            plot_data_bytes, meta_data = cloudflare_util.get_item_r2(PLOTS_BUCKET_NAME, f"{str(plot_id)}.dat")
            plot_data = PlotData.decode(plot_data_bytes)
            plot_data.verified = strtobool(meta_data.get("verified", "false"))

            chunk[str(plot_id)] = plot_data

        if chunk_id.is_base:

            # create point cloud
            samples = []

            for id, plot_data in chunk.items():
                
                plot_id = PlotId.from_hex(id)
                world_offset = np.array(plot_id_to_pos[plot_id.id])
                world_offset[1] += 1
                build_size = plot_data.build_data[1]
                expanded = utils.expand(plot_data.build_data)      
                cols = np.asarray(expanded)

                # Boolean mask: keep voxels that are “solid” *and* randomly chosen
                mask = (cols > PLOT_COUNT) & (np.random.rand(cols.size) < SAMPLE_PERCENTAGE[1] / 100)
                idxs = np.nonzero(mask)[0]           # indices of selected voxels

                if idxs.size:
                    xyz = utils.i2p_vec(idxs, build_size)
                    rgb = color_library.get_color_vec(cols[idxs])

                    xyz += 0.5
                    xyz /= build_size
                    xyz += world_offset

                    build_vects = np.hstack([xyz, rgb])   
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
        cloudflare_util.put_object(CHUNKS_BUCKET_NAME, f"{str(chunk_id)}.dat", encoded_chunk)

    except Exception as e:
        traceback.print_exc()
    


    