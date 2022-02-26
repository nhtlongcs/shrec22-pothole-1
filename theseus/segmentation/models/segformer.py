from typing import Dict, Any
from pyrsistent import freeze
import torch
import torch.nn as nn
import torch.nn.functional as F

"""
Source: https://github.com/qubvel/segmentation_models.pytorch
"""
from transformers import (
    SegformerConfig,
    SegformerForSemanticSegmentation,
)


class SegFormer(nn.Module):
    def __init__(
        self,
        pretrained: str = "nvidia/segformer-b0-finetuned-ade-512-512",
        num_classes: int = 1,
        freeze: bool = False,
        image_size=(512, 512),
        **kwargs
    ):
        super().__init__()
        self.num_classes = num_classes
        self.cfg = SegformerConfig().from_pretrained(pretrained)
        self.cfg.update({"output_hidden_states": False, "num_labels": num_classes})
        self.model = SegformerForSemanticSegmentation.from_pretrained(
            pretrained, config=self.cfg, ignore_mismatched_sizes=True,
        )
        self.image_size = image_size
        if freeze:
            self.freeze()

    def get_model(self):
        return self.model

    def grad_info(self):
        for name, param in self.model.named_parameters():
            print(name, param.requires_grad)

    def freeze(self):
        for param in self.model.model.parameters():
            param.requires_grad = False

    def forward(self, x):
        outputs = self.model(pixel_values=x)
        upscaled_logits = F.interpolate(outputs.logits, self.image_size, mode="nearest")
        return upscaled_logits

    def get_prediction(self, adict: Dict[str, Any], device: torch.device):
        inputs = adict["inputs"].to(device)
        outputs = self.forward(inputs)

        if self.num_classes == 1:
            thresh = adict["thresh"]
            predicts = (outputs > thresh).float()
        else:
            predicts = torch.argmax(outputs, dim=1)

        predicts = predicts.detach().cpu().squeeze().numpy()
        return {"masks": predicts}

