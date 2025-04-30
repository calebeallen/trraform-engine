
import redis
import os
import numpy as np
from sklearn.cluster import KMeans
from utils.constants import *
from utils import cloudflare_util
from utils.chunk import encode_chunk
from dotenv import load_dotenv
import sys
import traceback
import math

if os.getenv("ENV") != "prod":
    load_dotenv()

redis_cli = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    username=REDIS_USERNAME,
    password=os.getenv("REDIS_PASSWORD"),
    db=REDIS_DB,
)

LINEAR_THRESH = int(os.getenv("LINEAR_THRESH"))
SQRT_THRESH = int(os.getenv("SQRT_THRESH"))
LAYER_1_SAMPLE_PER = int(os.getenv("LAYER_1_SAMPLE_PER"))

def update_base_chunk(chunk_id):

    try:

        child_ids = chunk_id.get_base_children()
        layer = chunk_id.par_id

        samples = []
        chunk = {}

        # run k means for all point clouds
        for child_id in child_ids:
            
            child_id_str = str(child_id)

            try:
                points = np.load(f"./point_clouds/{child_id_str}.npy")
            except:
                continue

            N = len(points)
            if N < 2:
                continue

            if N >= 0 and N < LINEAR_THRESH:
                n_clusters = math.ceil(N / 2)
            elif N >= LINEAR_THRESH and N < SQRT_THRESH:
                offset = math.ceil(LINEAR_THRESH / 2) - math.ceil(math.sqrt(LINEAR_THRESH))
                n_clusters = math.ceil(math.sqrt(N)) + offset
            else:
                offset = math.ceil(LINEAR_THRESH / 2) - math.ceil(math.sqrt(LINEAR_THRESH)) + math.ceil(math.sqrt(SQRT_THRESH)) - math.ceil(math.log(SQRT_THRESH))
                n_clusters = math.ceil(math.log(N)) + offset

            xyz, rgb = points[:, :3], points[:, 3:]

            # normalize points for kmeans (rgb normalized already)
            xyz_min, xyz_max = xyz.min(0), xyz.max(0)
            den = np.where(xyz_max == xyz_min, 1, xyz_max - xyz_min)
            xyz_norm = (xyz - xyz_min) / den
            points_norm = np.hstack([xyz_norm, rgb])

            # run k means
            kmeans = KMeans(n_clusters=n_clusters, n_init="auto", random_state=0)
            labels = kmeans.fit_predict(points_norm)

            # create boxes for each cluster
            box_components = []
            for cid in range(n_clusters):

                # use original points
                xyz_cluster = xyz[labels == cid]
                rgb_cluster = rgb[labels == cid]

                mean_xyz = xyz_cluster.mean(axis=0)
                std_xyz = xyz_cluster.std(axis=0)

                # create box with bounds of 1 std from mean
                min_xyz = mean_xyz - std_xyz
                max_xyz = mean_xyz + std_xyz

                box_components.append(min_xyz)
                box_components.append(max_xyz)
                box_components.append(rgb_cluster.mean(axis=0))

            all_boxes = np.concatenate(box_components)  # Flattened 1D array
            box_bytes = all_boxes.astype(np.float32).tobytes()
            chunk[str(child_id)] = box_bytes

            # sample points for the next layer
            if chunk_id.par_id > 0:

                # get random sample of points SAMPLE_PERCENTAGE and append to samples
                sample_size = max(1, int(points.shape[0] * LAYER_1_SAMPLE_PER / 100))
                if sample_size > points.shape[0]:
                    sample_size = points.shape[0]

                sample_indices = np.random.choice(points.shape[0], sample_size, replace=False)
                samples.append(points[sample_indices])

        # store samples for next layer
        if samples:

            # store points for next layer to update
            points = np.vstack(samples)
            np.save(f"./point_clouds/{str(chunk_id)}", points)

            # flag next layer 
            parent_chunk_id = chunk_id.get_base_parent()
            redis_cli.sadd(f"needs_update:l{layer - 1}", str(parent_chunk_id))

        # push to cloudflare
        encoded_chunk = encode_chunk(chunk)
        cloudflare_util.put_object(CHUNKS_BUCKET_NAME, f"{str(chunk_id)}.dat", encoded_chunk)

    except Exception as e:
        print(e)
        traceback.print_exc()
    