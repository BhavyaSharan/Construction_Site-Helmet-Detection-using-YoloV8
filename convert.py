import os
import xml.etree.ElementTree as ET

input_dir = "datasets/annotations"
output_dir = "datasets/labels"
image_dir = "datasets/images"

os.makedirs(output_dir, exist_ok=True)

# Map helmet -> 0, head -> 1 ("no helmet")
class_map = {"helmet": 0, "head": 1}

for file in os.listdir(input_dir):
    if not file.endswith(".xml"):
        continue

    xml_file = os.path.join(input_dir, file)
    tree = ET.parse(xml_file)
    root = tree.getroot()

    img_filename = root.find("filename").text
    img_path = os.path.join(image_dir, img_filename)

    if not os.path.exists(img_path):
        print(f"⚠️ Image not found for {img_filename}, skipping...")
        continue

    size = root.find("size")
    W = int(size.find("width").text)
    H = int(size.find("height").text)

    labels = []

    for obj in root.iter("object"):
        cls_name = obj.find("name").text.lower()
        if cls_name not in class_map:
            continue  # ignore "person" class here

        cls = class_map[cls_name]

        bbox = obj.find("bndbox")
        xmin = float(bbox.find("xmin").text)
        xmax = float(bbox.find("xmax").text)
        ymin = float(bbox.find("ymin").text)
        ymax = float(bbox.find("ymax").text)

        x_center = ((xmin + xmax) / 2) / W
        y_center = ((ymin + ymax) / 2) / H
        width = (xmax - xmin) / W
        height = (ymax - ymin) / H

        labels.append(f"{cls} {x_center} {y_center} {width} {height}\n")

    label_file = os.path.join(output_dir, file.replace(".xml", ".txt"))
    with open(label_file, "w") as f:
        f.writelines(labels)

print("✅ Conversion complete! YOLO labels saved in: datasets/labels/")
