class Chunk:
    x:int
    z:int
    def __init__(self, x: int, y: int):
        self.x = x
        self.z = y

    def __repr__(self):
        return f"Chunk({self.x},{self.z})"