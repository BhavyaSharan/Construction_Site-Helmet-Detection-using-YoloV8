import os, random, shutil

image_dir = "datasets/images"
label_dir = "datasets/labels"

train_img = "datasets/train/images"
train_lbl = "datasets/train/labels"
val_img = "datasets/val/images"
val_lbl = "datasets/val/labels "

os.makedirs(train_img, exist_ok=True)
os.makedirs(train_lbl, exist_ok=True)
os.makedirs(val_img, exist_ok=True)
os.makedirs(val_lbl, exist_ok=True)

files = os.listdir(image_dir)
random.shuffle(files)

split_ratio = 0.8  # 80% train, 20% validation
train_count = int(len(files) * split_ratio)

for i, file in enumerate(files):
    if file.lower().endswith(('.jpg', '.png', '.jpeg')):
        src_img = os.path.join(image_dir, file)
        src_lbl = os.path.join(label_dir, file.rsplit(".",1)[0] + ".txt")

        if i < train_count:
            shutil.copy(src_img, train_img)
            shutil.copy(src_lbl, train_lbl)
        else:
            shutil.copy(src_img, val_img)
            shutil.copy(src_lbl, val_lbl)

print("✅ Dataset split complete!")
