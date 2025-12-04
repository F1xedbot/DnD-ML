import ZODB, ZODB.FileStorage
import persistent
from BTrees.OOBTree import OOBTree
import transaction
import os
from PIL import Image
import io
from core.models import ImageModel, LabelConfig

ImageModel = ImageModel
LabelConfig = LabelConfig

class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            # Default to 'mydata.fs' in the parent directory of 'core' (i.e., src/terrain_labeling)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "mydata.fs")
            
        self.storage = ZODB.FileStorage.FileStorage(db_path)
        self.db = ZODB.DB(self.storage)
        self.connection = self.db.open()
        self.root = self.connection.root()

        if not hasattr(self.root, 'images'):
            self.root.images = OOBTree()
        
        if not hasattr(self.root, 'labels'):
            self.root.labels = OOBTree()
            self._init_default_labels()
            
        transaction.commit()

    def _init_default_labels(self):
        defaults = {
            "grass":       {"walkable": True,  "slope_tolerance": 0.4},
            "dirt path":   {"walkable": True,  "slope_tolerance": 0.6},
            "rock wall":   {"walkable": False, "slope_tolerance": 0.1},
            "water":       {"walkable": False, "slope_tolerance": 0.1},
            "tree vegetation": {"walkable": False, "slope_tolerance": 0.1}
        }
        for name, config in defaults.items():
            if name not in self.root.labels:
                self.root.labels[name] = LabelConfig(name, **config)

    def add_image(self, image_path):
        filename = os.path.basename(image_path)
        with open(image_path, "rb") as f:
            image_data = f.read()
        image_model = ImageModel(filename, image_data)
        self.root.images[filename] = image_model
        transaction.commit()
        return filename

    def delete_image(self, name):
        if name in self.root.images:
            del self.root.images[name]
            transaction.commit()
            return True
        return False

    def get_all_images(self):
        return list(self.root.images.values())
    
    def get_image(self, name):
        return self.root.images.get(name)

    def update_image_analysis(self, name, relevant_labels, config):
        if name in self.root.images:
            img_model = self.root.images[name]
            img_model.relevant_labels = relevant_labels
            img_model.analysis_config = config
            img_model._p_changed = True
            transaction.commit()

    def update_image_tile_data(self, name, tile_data):
        if name in self.root.images:
            img_model = self.root.images[name]
            img_model.tile_data = tile_data
            img_model._p_changed = True
            transaction.commit()

    def add_label(self, name, walkable, slope_tolerance):
        if name in self.root.labels:
            return False
        self.root.labels[name] = LabelConfig(name, walkable, slope_tolerance)
        transaction.commit()
        return True

    def update_label(self, name, walkable, slope_tolerance):
        if name in self.root.labels:
            label = self.root.labels[name]
            label.walkable = walkable
            label.slope_tolerance = slope_tolerance
            transaction.commit()
            return True
        return False

    def delete_label(self, name):
        if name in self.root.labels:
            del self.root.labels[name]
            transaction.commit()
            return True
        return False

    def get_all_labels(self):
        return list(self.root.labels.values())

    def close(self):
        self.connection.close()
        self.db.close()
        self.storage.close()
