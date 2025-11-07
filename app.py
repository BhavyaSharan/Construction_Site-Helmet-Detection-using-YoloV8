import streamlit as st
from ultralytics import YOLO
import cv2
from PIL import Image
import numpy as np
import os
import time
import platform
import threading
import winsound

# --- Streamlit Configuration ---
st.set_page_config(page_title="Helmet Detection", layout="wide")
st.title("🪖 Helmet / No-Helmet Detection System")

# --- Load YOLOv8 Model ---
MODEL_PATH = "runs/detect/train3/weights/best.pt"
model = YOLO(MODEL_PATH)

# --- Sidebar Input ---
source = st.sidebar.radio("Select input source:", ["Upload Image", "Webcam"])

# --- Ensure violation folder exists ---
os.makedirs("violations", exist_ok=True)

# --- Buzzer Function ---
def play_alert_beep():
    """Plays two warning beeps."""
    if platform.system() == "Windows":
        for _ in range(5):
            winsound.Beep(2000, 300)
            time.sleep(0.2)  # Short delay between beeps
    else:
        for _ in range(5):
            os.system('play -nq -t alsa synth 0.3 sine 440')
            time.sleep(0.2)

# --- Session State for Alert Control ---
if 'last_alert_time' not in st.session_state:
    st.session_state.last_alert_time = 0

# --- IMAGE UPLOAD MODE ---
if source == "Upload Image":
    uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="Uploaded Image", use_column_width=True)
        
        # 🔧 Convert RGBA → RGB (fix 4-channel error)
        img_cv2 = np.array(img.convert("RGB"))

        # YOLO Detection
        results = model.predict(img_cv2)
        annotated = results[0].plot()
        st.image(annotated, caption="Detection Result", use_column_width=True)

        # Check if No Helmet Detected
        no_helmet_found = any(int(box.cls) == 1 for box in results[0].boxes)

        if no_helmet_found:
            st.warning("🚨 No Helmet Detected!")
            # Play alert beep
            play_alert_beep()
            
            timestamp = int(time.time())
            cv2.imwrite(f"violations/violation_{timestamp}.jpg", annotated)
            st.success("⚠ Violation image saved!")

# --- WEBCAM MODE ---
else:
    run = st.checkbox("Start Webcam")
    FRAME_WINDOW = st.image([])
    cap = cv2.VideoCapture(0)

    while run:
        ret, frame = cap.read()
        if not ret:
            st.warning("⚠ Cannot access webcam")
            break

        # 🔧 Ensure frame has 3 channels
        if frame.shape[-1] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        # YOLO detection
        results = model(frame)
        boxes = results[0].boxes

        helmet_count = 0
        no_helmet_count = 0
        no_helmet_detected = False

        for box in boxes:
            cls = int(box.cls)
            conf = float(box.conf)
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Adjust class IDs if reversed in your dataset
            if cls == 1 and conf > 0.3:
                no_helmet_detected = True
                no_helmet_count += 1
                color = (0, 0, 255)
                label = f"No Helmet ({conf:.2f})"
            elif cls == 0 and conf > 0.3:
                helmet_count += 1
                color = (0, 255, 0)
                label = f"Helmet ({conf:.2f})"
            else:
                continue

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # 🚨 Alert if no helmet detected
        if no_helmet_detected:
            st.warning("🚨 No Helmet Detected!")
            
            # Play alert beep with cooldown
            current_time = time.time()
            if current_time - st.session_state.last_alert_time >= 3:  # 3 second cooldown
                play_alert_beep()
                st.session_state.last_alert_time = current_time

            # Save violation image
            timestamp = int(time.time())
            cv2.imwrite(f"violations/violation_{timestamp}.jpg", frame)

        # Overlay live counts
        cv2.rectangle(frame, (10, 10), (260, 80), (0, 0, 0), -1)
        cv2.putText(frame, f"Helmet: {helmet_count}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"No Helmet: {no_helmet_count}", (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        FRAME_WINDOW.image(frame, channels="BGR")

    cap.release()
    # No need to clean up any threads as we're not using them anymore
