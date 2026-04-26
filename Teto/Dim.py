import string

from Iota.Chunk import Chunk
from Iota.Region import Region
from Zeta.Tools import build_hashmap_from_regions

from os import listdir
from os.path import isfile, join

class Dim:

    region_map: dict
    regions: list[Region] = []

    def __init__(self, path: string):
        self.path = path
        self.regions = []
        self.region_map = {}
        self.getRegions()

    def getRegions(self):
        regionFiles = [f for f in listdir(self.path) if isfile(join(self.path, f))]

        for regionFile in regionFiles:
            try:
                _, x, y, _ = regionFile.split(".")
                chunks = self.get_existing_chunks(join(self.path, regionFile))
                self.regions.append(Region(int(x), int(y), chunks))
            except ValueError:
                continue

        self.region_map = build_hashmap_from_regions(self.regions)

    def get_existing_chunks(self, path):
        chunks = []

        with open(path, "rb") as f:
            header = f.read(4096)

        for i in range(1024):
            entry = int.from_bytes(header[i * 4:i * 4 + 4], "big")

            if entry != 0:
                x = i % 32
                z = i // 32
                chunks.append(Chunk(x,z))

        return chunks
