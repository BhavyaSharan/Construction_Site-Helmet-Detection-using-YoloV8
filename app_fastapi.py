# app_fastapi.py
import io
import os
import time
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from ultralytics import YOLO
from PIL import Image
import numpy as np
import cv2
import base64

# ------------------------------------------------------------------------------
# FASTAPI CONFIGURATION
# ------------------------------------------------------------------------------
app = FastAPI(title="YOLOv8 Helmet Detection API")

# Allow all origins in dev; narrow in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# MODEL LOADING (using absolute path)
# ------------------------------------------------------------------------------
# Base directory = folder where this script resides
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Absolute path to best.pt
MODEL_PATH = os.path.join(
    BASE_DIR, "runs", "detect", "train3", "weights", "best.pt"
)

# Confirm file exists before loading
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model not found at: {MODEL_PATH}")

print(f"✅ Loading model from: {MODEL_PATH}")
model = YOLO(MODEL_PATH)  # load once at startup

# ------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------
def pil_from_bytes(b: bytes) -> Image.Image:
    return Image.open(io.BytesIO(b)).convert("RGB")


def boxes_to_json(boxes, model) -> List[dict]:
    out = []
    for box in boxes:
        xyxy = box.xyxy[0].tolist()
        conf = float(box.conf[0]) if hasattr(box, "conf") and len(box.conf) else float(box.conf)
        cls = int(box.cls[0]) if hasattr(box, "cls") and len(box.cls) else int(box.cls)
        out.append(
            {
                "bbox": [float(x) for x in xyxy],
                "confidence": conf,
                "class_id": cls,
                "label": model.names[cls] if hasattr(model, "names") else str(cls),
            }
        )
    return out


# ------------------------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "time": time.time()}


@app.post("/detect")
async def detect(file: UploadFile = File(...), annotated: bool = False):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    contents = await file.read()
    img = pil_from_bytes(contents)

    results = model(img)
    boxes = results[0].boxes if len(results) and hasattr(results[0], "boxes") else []
    detections = boxes_to_json(boxes, model)

    if annotated:
        annotated_np = results[0].plot()
        if isinstance(annotated_np, np.ndarray):
            if annotated_np.shape[-1] == 3:
                annotated_bgr = cv2.cvtColor(annotated_np, cv2.COLOR_RGB2BGR)
            else:
                annotated_bgr = annotated_np
            _, jpeg = cv2.imencode(".jpg", annotated_bgr)
            return StreamingResponse(io.BytesIO(jpeg.tobytes()), media_type="image/jpeg")
    return JSONResponse({"detections": detections})


@app.post("/detect_base64")
async def detect_base64(payload: dict):
    b64 = payload.get("b64") if isinstance(payload, dict) else None
    if not b64:
        raise HTTPException(status_code=400, detail="Missing 'b64' field.")

    if "," in b64:
        b64 = b64.split(",", 1)[1]

    img_bytes = base64.b64decode(b64)
    img = pil_from_bytes(img_bytes)

    results = model(img)
    boxes = results[0].boxes if len(results) and hasattr(results[0], "boxes") else []
    detections = boxes_to_json(boxes, model)
    return JSONResponse({"detections": detections})
