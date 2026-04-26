import string

from Iota import Chunk, Region

def chunk_key(chunk: Chunk) -> str:
    return f"{chunk.x},{chunk.z}"

def region_key(region: Region) -> str:
    return f"{region.rx},{region.ry}"

def chunk_world_rect(chunk: Chunk, region: Region, padding: int = 50, chunk_tile: int = 96):
    all_x = [c.x for c in region.chunks]
    all_y = [c.z for c in region.chunks]
    min_cx, min_cy = min(all_x), min(all_y)
    lx = chunk.x - min_cx
    ly = chunk.z - min_cy
    x1 = padding + lx * chunk_tile
    y1 = padding + ly * chunk_tile
    return x1, y1, x1 + chunk_tile, y1 + chunk_tile

def build_hashmap_from_regions(regions: list) -> dict:
    hm: dict = {}
    for r in regions:
        key = region_key(r)
        if key in hm:
            raise ValueError(f"Duplicate region at ({r.rx},{r.ry})")
        hm[key] = r
    return hm

def is_dimension(path: string) -> bool:
    split_path: list[str] = path.split("/")

    if split_path[-1] == "region" or split_path[-1].__contains__("DIM"):
        return True

    return False