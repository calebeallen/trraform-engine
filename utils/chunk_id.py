
import struct
from .plot_id import PlotId

chunk_maps_fwd = {}
chunk_maps_bwd = {}

# create layer 2 map
with open("./static/L2.dat", "rb") as file:

    bin = file.read()
    n = len(bin) // 4
    vals = list(struct.unpack(f'<{n}I', bin))
    chunk_map_l2_fwd = {} # from chunk to plot idx
    chunk_map_l2_bwd = {} # from plot idx to chunk

    for i in range(0, n, 2):

        p_id = vals[i]

        # fwd map
        if p_id not in chunk_map_l2_fwd:
            chunk_map_l2_fwd[p_id] = []

        # bwd map
        chunk_map_l2_fwd[p_id].append(i // 2)
        chunk_map_l2_bwd[i // 2] = p_id

    chunk_maps_fwd[2] = chunk_map_l2_fwd
    chunk_maps_bwd[2] = chunk_map_l2_bwd


# create layer 1 and layer 0 map
with open("./static/L1.dat", "rb") as file:

    bin = file.read()
    n = len(bin) // 4
    vals = list(struct.unpack(f'<{n}I', bin))
    chunk_map_l1_fwd = {} # from chunk to plot idx
    chunk_map_l1_bwd = {} # from plot idx to chunk
    chunk_map_l0_fwd = {0: []}
    chunk_map_l0_bwd = {}

    for i in range(0, n, 2):

        p_id = vals[i]
        c_id = vals[i+1]

        # fwd map
        if p_id not in chunk_map_l1_fwd:
            chunk_map_l1_fwd[p_id] = []
            chunk_map_l0_fwd[0].append(p_id)
            chunk_map_l0_bwd[p_id] = 0

        # bwd map
        chunk_map_l1_fwd[p_id].append(c_id)
        chunk_map_l1_bwd[c_id] = p_id

    chunk_maps_fwd[1] = chunk_map_l1_fwd
    chunk_maps_bwd[1] = chunk_map_l1_bwd
    chunk_maps_fwd[0] = chunk_map_l0_fwd
    chunk_maps_bwd[0] = chunk_map_l0_bwd


class ChunkId:

    def __init__(self, par_id: int, loc_id: int, is_base: bool):
        self.par_id = par_id
        self.loc_id = loc_id
        self.is_base = is_base

    @classmethod
    def from_plot_id(cls, plot_id: PlotId) -> "ChunkId":

        dep = plot_id.depth()

        if dep == 0:
            return cls(2, chunk_maps_bwd[2][plot_id.id - 1], True) 

        loc_id = plot_id.split()[-1]
        chunk_loc_id = (loc_id - 1) // 6
        par_id = plot_id.parent()
        return cls(par_id.id, chunk_loc_id, False)
    
    @classmethod
    def from_string(cls, string: str):

        split = string.split("_")
        if split[0][0] == "l":
            par_id = int(split[0][1], 16)
            is_base = True
        else:
            par_id = int(split[0], 16)
            is_base =  True

        return cls(par_id, int(split[1], 16), is_base)
        
    def get_base_parent(self) -> "ChunkId":

        par_loc_id = chunk_maps_bwd[self.par_id - 1][self.loc_id]
        return ChunkId(self.par_id - 1, par_loc_id, True)
    
    # children must be base chunks as well (layer < 2)
    def get_base_children(self) -> list["ChunkId"]:

        child_ids = [ChunkId(self.par_id + 1, loc, True) for loc in chunk_maps_fwd[self.par_id][self.loc_id]]
        return child_ids


    def __str__(self):
        
        if self.is_base:                    
            return f"l{self.par_id:x}_{self.loc_id:x}"
        return f"{self.par_id:x}_{self.loc_id:x}"  
