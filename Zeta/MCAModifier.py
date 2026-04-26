import os
import shutil

from Iota import Chunk

SECTOR_BYTES = 4096
HEADER_BYTES = 8192
CHUNK_COUNT = 1024

## Basically this entire method is AI because i didnt find a library that does this. i wonder why
def delete_chunks(
    path,
        rx:int , ry:int,
    chunks_to_delete,
    *,
    chunks_are_global=True,
    make_backup=True,
):
    path = path+"/"
    if make_backup:
        shutil.copy2(f"{path}r.{rx}.{ry}.mca",f"{path}r.{rx}.{ry}.mca.bak")

    def to_local(cx:int, cz:int):
        if chunks_are_global:
            return int(cx) - int(rx) * 32, int(cz) - int(ry) * 32
        return cx, cz

    delete_local = set()

    for chunk in chunks_to_delete:
        lx, lz = to_local(chunk.x, chunk.z)
        if 0 <= lx < 32 and 0 <= lz < 32:
            delete_local.add((lx, lz))

    tmp_path = f"{path}r.{rx}.{ry}.mca.tmp"

    new_locations = bytearray(SECTOR_BYTES)
    new_timestamps = bytearray(SECTOR_BYTES)

    deleted = 0
    next_sector = 2

    with open(f"{path}r.{rx}.{ry}.mca", "rb") as src, open(tmp_path, "wb") as dst:
        dst.write(b"\x00" * HEADER_BYTES)

        old_locations = src.read(SECTOR_BYTES)
        old_timestamps = src.read(SECTOR_BYTES)

        for index in range(CHUNK_COUNT):
            lx = index % 32
            lz = index // 32

            old_entry = old_locations[index * 4:index * 4 + 4]
            offset = int.from_bytes(old_entry[:3], "big")
            sector_count = old_entry[3]

            if offset == 0 or sector_count == 0:
                continue

            if (lx, lz) in delete_local:
                deleted += 1
                continue

            src.seek(offset * SECTOR_BYTES)
            chunk_bytes = src.read(sector_count * SECTOR_BYTES)

            if not chunk_bytes:
                continue

            dst.seek(next_sector * SECTOR_BYTES)
            dst.write(chunk_bytes)

            new_locations[index * 4:index * 4 + 3] = next_sector.to_bytes(3, "big")
            new_locations[index * 4 + 3] = sector_count

            new_timestamps[index * 4:index * 4 + 4] = old_timestamps[
                index * 4:index * 4 + 4
            ]

            next_sector += sector_count

        dst.seek(0)
        dst.write(new_locations)
        dst.write(new_timestamps)

        dst.truncate(next_sector * SECTOR_BYTES)

    os.remove(f"{path}r.{rx}.{ry}.mca")
    os.rename(tmp_path, f"{path}r.{rx}.{ry}.mca")

    return deleted

def deleteRegions(path: str, regions: list[str]):
    for region in regions:
        x, z = region.split(",")
        pathtomca=path+"/"+"r."+x+"."+z+".mca"
        if os.path.exists(pathtomca):
            os.remove(pathtomca)

    return