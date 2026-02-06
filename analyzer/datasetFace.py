import os
import json
import torch
from torch.utils.data import Dataset
from PIL import Image
from torchvision import transforms

class FaceLandmarkDataset(Dataset):
    def __init__(self, json_path, image_dir, transform=None):
        with open(json_path, 'r') as f:
            self.data = json.load(f)
        self.image_dir = image_dir
        self.transform = transform or transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor()
        ])
        
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        entry = self.data[idx]
        img_path = os.path.join(self.image_dir, entry["image"])
        image = Image.open(img_path).convert("RGB")
        w, h = image.size

        landmarks = torch.tensor(entry["landmarks"], dtype=torch.float32)
        landmarks[0::2] /= w  # нормализуем по ширине
        landmarks[1::2] /= h  # нормализуем по высоте

        image = self.transform(image)
        return image, landmarks
