# app_fastapi.py
import io
import os
import sys
import time
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from ultralytics import YOLO
from PIL import Image
import numpy as np
import cv2
import base64
from pathlib import Path
from datetime import datetime
import traceback
import requests
import platform

# ------------------ App setup ------------------
app = FastAPI(title="YOLOv8 Helmet Detection API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
VIOLATIONS_DIR = BASE_DIR / "violations"
VIOLATIONS_DIR.mkdir(parents=True, exist_ok=True)

# --------- Model path (adjust if needed) ----------
MODEL_PATH = BASE_DIR / "runs" / "detect" / "train3" / "weights" / "best.pt"
if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found at: {MODEL_PATH}")

print(f"✅ Loading model from: {MODEL_PATH}")
model = YOLO(str(MODEL_PATH))

# Telegram config (optional — leave None if not used)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None

print(f"[config] python: {sys.executable}")
print(f"[config] cwd: {os.getcwd()}")
print(f"[config] model.names: {getattr(model, 'names', None)}")
print(f"[config] TELEGRAM_API set? {bool(TELEGRAM_API)} TELEGRAM_CHAT_ID set? {bool(TELEGRAM_CHAT_ID)}")

# Simple in-memory cooldown
_last_notify_ts = 0
def should_notify(cooldown_seconds: int = 30) -> bool:
    global _last_notify_ts
    now = time.time()
    if now - _last_notify_ts > cooldown_seconds:
        _last_notify_ts = now
        return True
    return False

# ---------------- Helpers ----------------
def pil_from_bytes(b: bytes) -> Image.Image:
    return Image.open(io.BytesIO(b)).convert("RGB")

def boxes_to_json(boxes, model) -> List[dict]:
    """
    Simple, robust conversion of ultralytics Boxes -> list[dict].
    This mirrors the small working version you had (keeps it safe).
    """
    out = []
    try:
        for box in boxes:
            # attempt common access patterns
            try:
                xyxy = box.xyxy[0].tolist() if hasattr(box, "xyxy") and len(box.xyxy) else list(box.xyxy)
            except Exception:
                # fallback: try attribute directly or skip
                try:
                    xyxy = list(box.xyxy)
                except Exception:
                    xyxy = [0,0,0,0]
            # confidence
            try:
                conf = float(box.conf[0]) if hasattr(box, "conf") and len(getattr(box, "conf", [])) else float(getattr(box, "conf", 0.0))
            except Exception:
                conf = float(getattr(box, "confidence", 0.0)) if hasattr(box, "confidence") else 0.0
            # class
            try:
                cls = int(box.cls[0]) if hasattr(box, "cls") and len(getattr(box, "cls", [])) else int(getattr(box, "cls", 0))
            except Exception:
                cls = int(getattr(box, "class_id", 0)) if hasattr(box, "class_id") else 0
            label = model.names[cls] if hasattr(model, "names") and cls in model.names else str(cls)
            out.append({
                "bbox": [float(x) for x in xyxy],
                "confidence": float(conf),
                "class_id": int(cls),
                "label": str(label),
            })
    except Exception:
        # final fallback: empty list
        pass
    return out

def save_violation_image_from_pil(img_pil: Image.Image, prefix: str = "violation") -> str:
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}_{ts}.jpg"
        out_path = VIOLATIONS_DIR / filename
        arr = np.array(img_pil)
        if arr.ndim == 3 and arr.shape[2] == 3:
            bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        else:
            bgr = arr
        ok = cv2.imwrite(str(out_path), bgr)
        if not ok:
            print("[violation] cv2.imwrite returned False for", out_path)
            return ""
        print("[violation] saved:", out_path)
        return str(out_path)
    except Exception as e:
        print("Error saving violation image:", e)
        traceback.print_exc()
        return ""

# ---------------- Violation logic ----------------
def detect_violation(detections: List[dict],
                     min_helmet_conf: float = 0.35,
                     explicit_nohelmet_conf: float = 0.15) -> bool:
    """
    Decide violation using detection objects.
    - If explicit no_helmet class exists above threshold -> violation
    - If no explicit person class in model, we consider presence of any detection (with decent conf)
      as a person proxy. Helmet presence needs to be >= min_helmet_conf to avoid false positives.
    """
    if not detections:
        return False

    # Normalize labels and confidences
    dets = [{"label": (d.get("label") or "").lower(), "conf": float(d.get("confidence", 0.0)), "bbox": d.get("bbox", [])} for d in detections]
    print("[detect_violation] detections:", [(d["label"], round(d["conf"], 3)) for d in dets])

    # explicit 'no_helmet' -> immediate violation (your data.yaml has 'no_helmet' class)
    explicit_nohelmet_keywords = ("nohelmet", "no_helmet", "no-helmet", "withouthelmet", "without_helmet")
    for d in dets:
        if any(k == d["label"] or k in d["label"] for k in explicit_nohelmet_keywords) and d["conf"] >= explicit_nohelmet_conf:
            print("[detect_violation] explicit no_helmet detected:", d)
            return True

    # helmet present?
    helmet_keywords = ("helmet", "hardhat", "with_hat", "withhelmet", "hat")
    helmet_present = any((any(k == d["label"] or k in d["label"] for k in helmet_keywords) and d["conf"] >= min_helmet_conf) for d in dets)

    # person present? (only if your model actually has person class)
    person_keywords = ("person", "worker", "man", "woman")
    person_present = any((any(k == d["label"] or k in d["label"] for k in person_keywords) and d["conf"] >= 0.3) for d in dets)

    # If no explicit person class in data.yaml (your model has only helmet/no_helmet),
    # consider presence of any detection with moderate conf as a proxy for a person.
    if not person_present:
        any_person_like = any(d["conf"] >= 0.3 for d in dets)
        if any_person_like:
            person_present = True
            print("[detect_violation] no person class; using any detection as person proxy")

    print(f"[detect_violation] person_present={person_present}, helmet_present={helmet_present}")
    return person_present and not helmet_present

# ---------------- Telegram helpers (optional) ----------------
def send_telegram_text(message: str) -> bool:
    if not TELEGRAM_API or not TELEGRAM_CHAT_ID:
        print("Telegram not configured")
        return False
    url = f"{TELEGRAM_API}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode":"HTML"}, timeout=10)
        print("Telegram text response:", resp.status_code, resp.text)
        return resp.ok
    except Exception as e:
        print("send_telegram_text error:", e)
        return False

def send_telegram_photo(image_path: str, caption: str = None) -> bool:
    if not TELEGRAM_API or not TELEGRAM_CHAT_ID:
        print("Telegram not configured")
        return False
    url = f"{TELEGRAM_API}/sendPhoto"
    try:
        with Image.open(image_path) as im:
            max_dim = 1600
            if max(im.size) > max_dim:
                im.thumbnail((max_dim, max_dim), Image.ANTIALIAS)
                tmp = str(image_path) + ".tmp.jpg"
                im.save(tmp, format="JPEG", quality=85)
                send_path = tmp
            else:
                send_path = image_path
        with open(send_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": TELEGRAM_CHAT_ID}
            if caption:
                data["caption"] = caption
                data["parse_mode"] = "HTML"
            resp = requests.post(url, data=data, files=files, timeout=30)
        if send_path.endswith(".tmp.jpg") and os.path.exists(send_path):
            try:
                os.remove(send_path)
            except Exception:
                pass
        print("Telegram photo response:", resp.status_code, resp.text)
        return resp.ok
    except Exception as e:
        print("send_telegram_photo error:", e)
        return False

def notify_violation_async(image_path: str, labels: list):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        caption = f"⚠️ <b>Helmet Violation</b>\nTime: {ts}\nDetections: {', '.join(labels) if labels else 'N/A'}"
        send_telegram_text(caption)
        send_telegram_photo(image_path, caption="Violation image")
    except Exception as e:
        print("notify_violation_async error:", e)

# ---------------- Routes ----------------
@app.get("/health")
def health():
    return {"status":"ok", "time":time.time()}

@app.get("/info")
def info():
    return {
        "python_executable": sys.executable,
        "cwd": os.getcwd(),
        "model_names": str(getattr(model, "names", None)),
        "telegram": {"token_present": bool(TELEGRAM_TOKEN), "chat_id_present": bool(TELEGRAM_CHAT_ID)}
    }

@app.post("/detect")
async def detect(file: UploadFile = File(...), annotated: bool = False, save_violation: bool = True, debug_force_notify: bool = False, background_tasks: BackgroundTasks = None):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    contents = await file.read()
    img_pil = pil_from_bytes(contents)

    # ---- IMPORTANT: use PIL input (same as your working shorter script) ----
    try:
        # use default confidence (let ultralytics default or set to 0.25-0.3)
        results = model(img_pil, conf=0.25, iou=0.45)
    except Exception as e:
        print("Model inference error:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Model inference failed")

    boxes = results[0].boxes if len(results) and hasattr(results[0], "boxes") else []
    detections = boxes_to_json(boxes, model)
    labels = [d["label"].lower() for d in detections]
    print("[detect] labels:", labels)
    print("[detect] raw detections:", detections)

    violation_saved_path = ""
    try:
        if save_violation:
            violation_detected = detect_violation(detections, min_helmet_conf=0.35, explicit_nohelmet_conf=0.15)
            print("[detect] violation_detected:", violation_detected)
            if violation_detected:
                # produce annotated image if possible
                annotated_np = None
                try:
                    annotated_np = results[0].plot()
                except Exception as e:
                    print("[detect] plot error:", e)
                    annotated_np = None

                if isinstance(annotated_np, np.ndarray):
                    if annotated_np.shape[-1] == 3:
                        annotated_bgr = cv2.cvtColor(annotated_np, cv2.COLOR_RGB2BGR)
                    else:
                        annotated_bgr = annotated_np
                    pil_ann = Image.fromarray(cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB))
                    violation_saved_path = save_violation_image_from_pil(pil_ann, prefix="violation_annot")
                else:
                    violation_saved_path = save_violation_image_from_pil(img_pil, prefix="violation")
    except Exception as e:
        print("Error during violation detection/save:", e)
        traceback.print_exc()

    # schedule notification if needed
    if violation_saved_path and (debug_force_notify or should_notify(30)):
        if background_tasks is not None:
            background_tasks.add_task(notify_violation_async, violation_saved_path, labels)
        else:
            notify_violation_async(violation_saved_path, labels)

    if annotated:
        annotated_np = None
        try:
            annotated_np = results[0].plot()
        except Exception:
            annotated_np = None
        if isinstance(annotated_np, np.ndarray):
            if annotated_np.shape[-1] == 3:
                annotated_bgr = cv2.cvtColor(annotated_np, cv2.COLOR_RGB2BGR)
            else:
                annotated_bgr = annotated_np
            _, jpeg = cv2.imencode(".jpg", annotated_bgr)
            return StreamingResponse(io.BytesIO(jpeg.tobytes()), media_type="image/jpeg")

    return JSONResponse({"detections": detections, "violation_saved": violation_saved_path})

@app.post("/detect_base64")
async def detect_base64(payload: dict, save_violation: bool = True, background_tasks: BackgroundTasks = None):
    b64 = payload.get("b64") if isinstance(payload, dict) else None
    if not b64:
        raise HTTPException(status_code=400, detail="Missing 'b64' field.")
    if "," in b64:
        b64 = b64.split(",", 1)[1]
    img_bytes = base64.b64decode(b64)
    img_pil = pil_from_bytes(img_bytes)
    try:
        results = model(img_pil, conf=0.25, iou=0.45)
    except Exception as e:
        print("Model inference error:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Model inference failed")
    boxes = results[0].boxes if len(results) and hasattr(results[0], "boxes") else []
    detections = boxes_to_json(boxes, model)
    labels = [d["label"].lower() for d in detections]
    violation_saved_path = ""
    try:
        if save_violation and detect_violation(detections, min_helmet_conf=0.35, explicit_nohelmet_conf=0.15):
            annotated_np = None
            try:
                annotated_np = results[0].plot()
            except Exception:
                annotated_np = None
            if isinstance(annotated_np, np.ndarray):
                if annotated_np.shape[-1] == 3:
                    annotated_bgr = cv2.cvtColor(annotated_np, cv2.COLOR_RGB2BGR)
                else:
                    annotated_bgr = annotated_np
                pil_ann = Image.fromarray(cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB))
                violation_saved_path = save_violation_image_from_pil(pil_ann, prefix="violation_annot")
            else:
                violation_saved_path = save_violation_image_from_pil(img_pil, prefix="violation")
    except Exception as e:
        print("Error during violation detection/save:", e)
        traceback.print_exc()
    if violation_saved_path and should_notify(30):
        if background_tasks is not None:
            background_tasks.add_task(notify_violation_async, violation_saved_path, labels)
        else:
            notify_violation_async(violation_saved_path, labels)
    return JSONResponse({"detections": detections, "violation_saved": violation_saved_path})

@app.get("/test_telegram")
def test_telegram():
    ok_text = send_telegram_text("Test message from YOLOv8 backend ✅")
    ok_photo = False
    test_img = VIOLATIONS_DIR / "test_notify.jpg"
    if test_img.exists():
        ok_photo = send_telegram_photo(str(test_img), "Test image from YOLOv8 backend")
    return {"text_sent": ok_text, "photo_sent": ok_photo}
