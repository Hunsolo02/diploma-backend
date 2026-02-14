import torch.nn as nn
import torchvision.models as models
from torchvision.models import ResNet18_Weights


class LandmarkModel(nn.Module):
    def __init__(self, num_points):
        super().__init__()

        # Backbone
        self.backbone = models.resnet18(
            weights=ResNet18_Weights.DEFAULT
        )

        in_features = self.backbone.fc.in_features

        # ГОЛОВА РЕГРЕССИИ
        self.backbone.fc = nn.Sequential(
            nn.Linear(in_features, num_points * 2),
            nn.Sigmoid()   # 🔥 КРИТИЧЕСКИ ВАЖНО
        )

    def forward(self, x):
        return self.backbone(x)
