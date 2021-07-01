import cv2
import torch
import argparse
import numpy as np
from torchvision import models
from albumentations import Resize, Compose
from albumentations.pytorch.transforms import ToTensor
from albumentations.augmentations.transforms import Normalize


def preprocess_image(img_path):
    # transformations for the input data
    transforms = Compose([
        Resize(224, 224, interpolation=cv2.INTER_NEAREST),
        Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensor(),
    ])
    # read input image
    input_img = cv2.imread(img_path)
    # do transformations
    input_data = transforms(image=input_img)["image"]

    batch_data = torch.unsqueeze(input_data, 0)
    return batch_data


def postprocess(output_data):
    # get class names
    with open("imagenet_classes.txt") as f:
        classes = [line.strip() for line in f.readlines()]
    # calculate human-readable value by softmax
    confidences = torch.nn.functional.softmax(output_data, dim=1)[0] * 100
    # find top predicted classes
    _, indices = torch.sort(output_data, descending=True)
    i = 0
    # print the top classes predicted by the model
    while confidences[indices[0][i]] > 0.5:
        class_idx = indices[0][i]
        print(
            "class:",
            classes[class_idx],
            ", confidence:",
            confidences[class_idx].item(),
            "%, index:",
            class_idx.item(),
        )
        i += 1


def main(args):
    inp = preprocess_image("turkish_coffee.jpg")
    print(inp.shape)
    model = models.resnet50(pretrained=True)
    model.eval()
    with torch.no_grad():
        output = model(inp)
        print(output.shape)
        postprocess(output)

    if args.build_onnx:
        print("build onnx ...")
        dynamic_axes = {"input": {0: "batch"}, "output": {0: "batch"}}
        torch.onnx.export(
            model,
            inp,
            args.onnx_path,
            input_names=["input"],
            output_names=["output"],
            export_params=True,
            dynamic_axes=dynamic_axes
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resnet50")
    parser.add_argument("--pretrained", action="store_true", default=True)
    parser.add_argument('--build-onnx', action="store_true")
    parser.add_argument("--onnx-path", type=str, default='resnet50_dynamic_shape.onnx')
    parser.add_argument('--build-engine', action="store_true")
    parser.add_argument("--engine-path", type=str, default='test.engine')
    args = parser.parse_args()
    main(args)
