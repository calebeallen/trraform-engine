
import numpy as np
from sklearn.cluster import KMeans
import struct
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def create_map(layer, n, chunk_ids, points):

    kmeans = KMeans(n_clusters=n, random_state=0)
    labels = kmeans.fit_predict(points)

    c1id_cid = {}
    
    for i, c1id in enumerate(labels):

        if c1id not in c1id_cid:
            c1id_cid[c1id] = []

        c1id_cid[c1id].append(chunk_ids[i])

    # flatten map
    flat = ""
    for c1id in c1id_cid:
        for cid in c1id_cid[c1id]:
            flat += f"{c1id}:{cid}\n"

    # write map
    with open(f"./L{layer}.txt", "w") as file:
        file.write(flat)
        file.close()

    next_ids = [str(i) for i, _ in enumerate(kmeans.cluster_centers_)]

    return next_ids, kmeans.cluster_centers_

def i2p(idx, size):

    s2 = size * size
    return [ idx % size, int(idx / s2), int( (idx % s2 ) / size ) ]

build_size = 0

with open("./0x00.dat", "rb") as file:

    data = file.read()
    n = len(data) // 2
    condensed = list(struct.unpack(f"{n}H", data))
    build_size = condensed[1]
    file.close()


# create a mapping for chunk id => plot positions in the chunk
chunk_map = {}
with open("./L2.txt", "r") as file:

    lines = file.readlines()
    for line in lines:
        chunk_id, idx = line.split(":")

        if chunk_id not in chunk_map:
            chunk_map[chunk_id] = []

        chunk_map[chunk_id].append(i2p(int(idx), build_size))


chunk_ids = list(chunk_map.keys())
points = np.array([np.mean(chunk_map[cid], axis=0) for cid in chunk_ids])

chunk_ids, points = create_map(1, 87, chunk_ids, points)



# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')

# # Plot each point with its cluster color
# for i, point in enumerate(points):
#     ax.scatter(point[0], point[1], point[2], c=f"C{labels[i]}", label=f"Cluster {labels[i]}" if i == 0 else "")

# # Optional: Plot centroids
# centroids = kmeans.cluster_centers_
# ax.scatter(
#     centroids[:, 0],
#     centroids[:, 1],
#     centroids[:, 2],
#     s=100,
#     c='black',
#     marker='x',
#     label='Centroids'
# )

# ax.set_title("3D K-means Clustering")
# ax.set_xlabel("X")
# ax.set_ylabel("Y")
# ax.set_zlabel("Z")
# plt.legend()
# plt.show()



# with open("./L2_R.txt", "r") as f:
#     lines = f.readlines()

# # Sort based on the integer before the colon
# sorted_lines = sorted(lines, key=lambda line: int(line.split(":")[0]))

# with open("./L2.txt", "w") as f:
#     f.writelines(sorted_lines)