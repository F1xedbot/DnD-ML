import persistent

class ImageModel(persistent.Persistent):
    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.relevant_labels = []
        self.analysis_config = {}
        self.tile_data = {}

class LabelConfig(persistent.Persistent):
    def __init__(self, name, walkable=True, slope_tolerance=0.5):
        self.name = name
        self.walkable = walkable
        self.slope_tolerance = slope_tolerance
