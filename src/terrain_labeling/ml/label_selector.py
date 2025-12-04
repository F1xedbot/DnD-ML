import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel


class LabelSelector:
    def __init__(self):
        print("Initializing LabelSelector (Lazy Loading)...")
        self.model = None
        self.processor = None
        self._initialized = True

    def _load_model(self):
        if self.model is None:
            print("Loading CLIP Model...")
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            print("CLIP Model Loaded.")

    def analyze(self, image_path, labels, prompt_template, top_k=5, threshold=0.2):
        self._load_model()
        
        if not labels:
            return []

        # Prepare Text Features
        text_inputs = [prompt_template.format(l) for l in labels]
        inputs = self.processor(text=text_inputs, return_tensors="pt", padding=True)
        
        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)
            text_features /= text_features.norm(dim=-1, keepdim=True)

        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            print(f"Error opening image {image_path}: {e}")
            return []

        w, h = image.size
        crops = [
            image,                            # Global
            image.crop((0, 0, w//2, h//2)),   # Top-Left
            image.crop((w//2, 0, w, h//2)),   # Top-Right
            image.crop((0, h//2, w//2, h)),   # Bottom-Left
            image.crop((w//2, h//2, w, h))    # Bottom-Right
        ]

        inputs = self.processor(images=crops, return_tensors="pt", padding=True)

        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
            image_features /= image_features.norm(dim=-1, keepdim=True)

            similarity = (image_features @ text_features.T)
            
            # Max-Pooling across views
            max_scores, _ = similarity.max(dim=0) # Shape: (N,)

        top_indices = max_scores.argsort(descending=True)[:top_k]
        
        results = []
        for idx in top_indices:
            score = max_scores[idx].item()
            if score > threshold:
                results.append({'name': labels[idx], 'score': score})
        
        return results
