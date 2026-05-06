"""
 * Image Encoding using ResNet18.
 """
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
from app.config import IMG_DIM

class ImageEncoder:
    """
     * Encoder for satellite image patches using a pre-trained CNN.
     """
    def __init__(self):
        """
         * Initialize the ResNet18 model and transformation pipeline.
         """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load pre-trained ResNet18
        self.model = models.resnet18(weights='DEFAULT')
        
        # Replace the final fully connected layer to output IMG_DIM features
        self.model.fc = torch.nn.Linear(self.model.fc.in_features, IMG_DIM)
        
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # Standard ImageNet transformations
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

    def encode(self, image_path: str) -> np.ndarray:
        """
         * Encode a single image into a feature vector.
         * @param {str} image_path - Path to the image file
         * @returns {np.ndarray} A 1D array of shape (IMG_DIM,)
         """
        try:
            img = Image.open(image_path).convert('RGB')
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return np.zeros(IMG_DIM, dtype=np.float32)
            
        img_t = self.transform(img).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            emb = self.model(img_t).squeeze().cpu().numpy()
            
        return emb.astype(np.float32)

    def encode_batch(self, image_paths: list[str]) -> np.ndarray:
        """
         * Encode N images in one forward pass.
         * @param {list[str]} image_paths - List of image file paths
         * @returns {np.ndarray} A 2D array of shape (N, IMG_DIM)
         """
        tensors = []
        valid_paths = []
        
        for path in image_paths:
            try:
                img = Image.open(path).convert('RGB')
                tensors.append(self.transform(img))
                valid_paths.append(path)
            except Exception as e:
                print(f"Error loading image {path}: {e}")
                tensors.append(torch.zeros(3, 224, 224))
                valid_paths.append(path)
        
        if not tensors:
            return np.zeros((0, IMG_DIM), dtype=np.float32)
        
        batch = torch.stack(tensors).to(self.device)
        
        with torch.no_grad():
            embeddings = self.model(batch).cpu().numpy()
        
        return embeddings.astype(np.float32)
