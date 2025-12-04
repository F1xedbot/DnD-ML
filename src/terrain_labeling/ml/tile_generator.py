import torch
import numpy as np
from PIL import Image
from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation, pipeline

import io
import matplotlib.pyplot as plt
import matplotlib.cm as cm

class TileGenerator:
    def __init__(self):
        print("Initializing TileGenerator (Lazy Loading)...")
        self.processor = None
        self.segment_model = None
        self.depth_pipe = None
        self._initialized = True

    def _load_models(self):
        if self.segment_model is None:
            print("Loading CLIPSeg and Depth Models...")
            self.processor = CLIPSegProcessor.from_pretrained("CIDAS/clipseg-rd64-refined")
            self.segment_model = CLIPSegForImageSegmentation.from_pretrained("CIDAS/clipseg-rd64-refined")
            self.depth_pipe = pipeline(task="depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
            print("Models Loaded.")

    def _get_slope_map(self, depth_map):
        dy, dx = np.gradient(depth_map)
        slope_magnitude = np.sqrt(dx**2 + dy**2)
        return slope_magnitude / (np.max(slope_magnitude) + 1e-8)

    def _process_full_image(self, image_path, labels):
        self._load_models()
        print("Running AI Inference...")
        image = Image.open(image_path).convert("RGB")
        original_size = image.size 
        
        inputs = self.processor(text=labels, images=[image] * len(labels), padding=True, return_tensors="pt")
        with torch.no_grad():
            outputs = self.segment_model(**inputs)
        logits = outputs.logits.detach().cpu()
        
        # logits shape: (num_labels, height, width) or (height, width) if 1 label
        if len(labels) == 1:
            logits = logits.unsqueeze(0)
            
        logits_resized = torch.nn.functional.interpolate(
            logits.unsqueeze(1), size=(original_size[1], original_size[0]), mode="bilinear"
        ).squeeze(1)
        
        mat_map = torch.argmax(torch.sigmoid(logits_resized), dim=0).numpy()
        
        depth_result = self.depth_pipe(image)
        depth_map = np.array(depth_result["depth"]) / 255.0
        slope_map = self._get_slope_map(depth_map)
        
        return image, mat_map, slope_map

    @staticmethod
    def analyze_tile_logic(composition, slope_val, label_configs, walkability_threshold):
        if not composition:
            return False, "no_data", "none"
            
        dominant_label = max(composition, key=composition.get)
        mat_config = label_configs.get(dominant_label, {"walkable": False, "slope_tolerance": 0.1})

        walkable_ratio = 0.0
        for label, percent in composition.items():
            px_conf = label_configs.get(label, {"walkable": False})
            if px_conf["walkable"]:
                walkable_ratio += percent

        is_material_walkable = walkable_ratio >= walkability_threshold

        dynamic_limit = mat_config["slope_tolerance"]
        is_physically_steep = slope_val > dynamic_limit
        
        if not is_material_walkable:
            return False, "bad_material", dominant_label
        elif is_physically_steep:
            return False, "steep_slope", dominant_label
        else:
            return True, "none", dominant_label

    def generate(self, image_path, labels, rows, cols, label_configs=None, walkability_threshold=0.4):
        try:
            image, mat_map, slope_map = self._process_full_image(image_path, labels)
            img_w, img_h = image.size
            tile_w = img_w // cols
            tile_h = img_h // rows

            tile_data = []
            
            if label_configs is None:
                label_configs = {} 

            print("Generating Level Data...")
            for row in range(rows):
                for col in range(cols):
                    
                    # Define Tile Area
                    x0, y0 = col * tile_w, row * tile_h
                    x1, y1 = x0 + tile_w, y0 + tile_h
                    
                    # Extract Data
                    tile_mat = mat_map[y0:y1, x0:x1]
                    tile_slope = slope_map[y0:y1, x0:x1]
                    
                    if tile_mat.size == 0: continue

                    unique, counts = np.unique(tile_mat, return_counts=True)
                    counts_dict = dict(zip(unique, counts))
                    total_pixels = tile_mat.size
                    
                    composition = {}
                    
                    for idx, label in enumerate(labels):
                        count = counts_dict.get(idx, 0)
                        if count > 0:
                            percent = round(count / total_pixels, 3)
                            composition[label] = percent
                    
                    # Inner Sanctum logic
                    margin_x = max(1, int(tile_w * 0.25))
                    margin_y = max(1, int(tile_h * 0.25))
                    inner_slope = tile_slope[margin_y:-margin_y, margin_x:-margin_x]
                    if inner_slope.size == 0: inner_slope = tile_slope
                    
                    max_slope_val = float(np.max(inner_slope))
                    
                    walkable, block_reason, dominant = self.analyze_tile_logic(
                        composition, max_slope_val, label_configs, walkability_threshold
                    )

                    tile_entry = {
                        "id": f"tile_{col}_{row}",
                        "grid_pos": [col, row],
                        "world_pos": [x0, y0],
                        "composition": composition, 
                        "slope_val": round(max_slope_val, 3),
                        "walkable": walkable,
                        "block_reason": block_reason,
                        "dominant": dominant
                    }
                    tile_data.append(tile_entry)
            
            maps = {}
            try:
                with io.BytesIO() as bio:
                    image.save(bio, format="PNG")
                    maps["original"] = bio.getvalue()

                # Material Map (Colored)
                if mat_map.max() > 0:
                    norm_mat = mat_map / (mat_map.max() + 1e-8)
                else:
                    norm_mat = mat_map
                
                # Use a colormap (e.g., 'tab10' or 'viridis')
                cmap = cm.get_cmap('tab10')
                colored_mat = cmap(norm_mat) # Returns RGBA
                # Convert to PIL (uint8)
                colored_mat_uint8 = (colored_mat[:, :, :3] * 255).astype(np.uint8)
                pil_mat = Image.fromarray(colored_mat_uint8)
                with io.BytesIO() as bio:
                    pil_mat.save(bio, format="PNG")
                    maps["material"] = bio.getvalue()

                # Slope Map (Grayscale)
                slope_uint8 = (slope_map * 255).astype(np.uint8)
                pil_slope = Image.fromarray(slope_uint8, mode="L")
                with io.BytesIO() as bio:
                    pil_slope.save(bio, format="PNG")
                    maps["slope"] = bio.getvalue()
            except Exception as e:
                print(f"Map generation warning: {e}")

            return {
                "config": {"rows": rows, "cols": cols},
                "data": tile_data,
                "maps": maps
            }

        except Exception as e:
            print(f"Error in generate: {e}")
            import traceback
            traceback.print_exc()
            return None
