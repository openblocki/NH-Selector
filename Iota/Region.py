from Zeta.Tools import chunk_key


class Region:
    chunk_map: dict
    def __init__(self, rx: int, ry: int, chunks: list):
        self.rx     = rx
        self.ry     = ry
        self.chunks = chunks
        self._chunk_map: dict = {chunk_key(c): c for c in chunks}

    def __repr__(self):
        return f"Region({self.rx},{self.ry}, {len(self.chunks)} chunks)"
