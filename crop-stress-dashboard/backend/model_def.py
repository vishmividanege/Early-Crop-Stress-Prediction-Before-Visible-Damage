import torch.nn as nn
from torchvision.models import resnet18

def build_resnet18_6ch(num_classes=2):
    model = resnet18(weights=None)

    model.conv1 = nn.Conv2d(
        6, model.conv1.out_channels,
        kernel_size=model.conv1.kernel_size,
        stride=model.conv1.stride,
        padding=model.conv1.padding,
        bias=False
    )

    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model
