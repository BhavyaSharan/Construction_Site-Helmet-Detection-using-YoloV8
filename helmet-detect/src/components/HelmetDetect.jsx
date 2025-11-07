import React, { useRef, useState, useEffect } from "react";
import Webcam from "react-webcam";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { Howl } from "howler";

const HelmetDetect = () => {
  const webcamRef = useRef(null);
  const [detections, setDetections] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [uploadedDetections, setUploadedDetections] = useState([]);
  const [statusMessage, setStatusMessage] = useState("Waiting for detection...");
  const [statusKey, setStatusKey] = useState("waiting");

  const API_URL = "http://localhost:8000/detect_base64"; // FastAPI endpoint

  // Sounds
  const warningSound = new Howl({
    src: ["https://actions.google.com/sounds/v1/alarms/beep_short.ogg"],
    volume: 0.8,
  });

  const successSound = new Howl({
    src: ["https://actions.google.com/sounds/v1/cartoon/cartoon_boing.ogg"],
    volume: 0.5,
  });

  // Detect function
  const detectFrame = async (base64, isUpload = false) => {
    try {
      const response = await axios.post(API_URL, { b64: base64 });
      const data = response.data.detections || [];

      if (isUpload) setUploadedDetections(data);
      else setDetections(data);

      const noHelmet = data.some(
        (d) =>
          d.label.toLowerCase().includes("no") ||
          d.label.toLowerCase().includes("without")
      );

      if (data.length === 0) {
        setStatusMessage("Waiting for detection...");
        setStatusKey("waiting");
      } else if (noHelmet) {
        setStatusMessage("⚠️ No helmet detected! Please wear one.");
        setStatusKey("alert");
        warningSound.play();
      } else {
        setStatusMessage("✅ All riders wearing helmets.");
        setStatusKey("safe");
        successSound.play();
      }
    } catch (err) {
      console.error("Detection error:", err);
    }
  };

  // Live detection loop
  useEffect(() => {
    let interval;
    if (isRunning) {
      interval = setInterval(async () => {
        if (webcamRef.current) {
          const imageSrc = webcamRef.current.getScreenshot();
          if (imageSrc) await detectFrame(imageSrc);
        }
      }, 1000);
    } else if (interval) {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  // Handle upload detection
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onloadend = async () => {
      const base64 = reader.result;
      setUploadedImage(base64);
      setLoading(true);
      await detectFrame(base64, true);
      setLoading(false);
    };
    reader.readAsDataURL(file);
  };

  // Determine border color (feedback)
  const borderClass =
    detections.length === 0
      ? "border-blue-400/40 shadow-blue-400/20"
      : detections.some(
          (d) =>
            d.label.toLowerCase().includes("no") ||
            d.label.toLowerCase().includes("without")
        )
      ? "border-red-500 animate-pulse shadow-red-500/40"
      : "border-green-400 shadow-green-400/40";

  return (
    <section
      id="detect"
      className="flex flex-col items-center justify-center py-24 px-4 text-center relative"
    >
      <h2 className="text-3xl md:text-5xl font-bold fancy-text mb-6">
        Live Helmet Detection
      </h2>
      <p className="text-gray-300 mb-8 max-w-xl">
        Detect helmets in real time using your webcam or upload an image below.
      </p>

      {/* Live webcam section */}
      <div
        className={`relative w-[90%] md:w-[640px] rounded-2xl overflow-hidden border-4 transition-all duration-700 ${borderClass}`}
      >
        <Webcam
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          className="rounded-2xl"
          mirrored={true}
        />

        {/* Bounding boxes */}
        {detections.map((det, i) => {
          const [x1, y1, x2, y2] = det.bbox;
          const color =
            det.label.toLowerCase().includes("no") ||
            det.label.toLowerCase().includes("without")
              ? "red"
              : "green";
          return (
            <div
              key={i}
              className={`absolute border-2 border-${color}-400`}
              style={{
                top: y1,
                left: x1,
                width: x2 - x1,
                height: y2 - y1,
              }}
            >
              <span
                className={`absolute top-0 left-0 px-1 text-xs font-bold rounded-br-md ${
                  color === "red"
                    ? "bg-red-500 text-white"
                    : "bg-green-400 text-black"
                }`}
              >
                {det.label} ({Math.round(det.confidence * 100)}%)
              </span>
            </div>
          );
        })}
      </div>

      {/* Status message with animation */}
      <div className="h-10 mt-4">
        <AnimatePresence mode="wait">
          <motion.p
            key={statusKey}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.4 }}
            className={`font-semibold text-lg ${
              statusKey === "waiting"
                ? "text-blue-400"
                : statusKey === "alert"
                ? "text-red-500"
                : "text-green-400"
            }`}
          >
            {statusMessage}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* Controls */}
      <div className="mt-6 flex flex-col md:flex-row gap-4">
        <motion.button
          onClick={() => setIsRunning(!isRunning)}
          whileTap={{ scale: 0.95 }}
          className={`px-6 py-3 font-semibold rounded-full shadow-md transition-all ${
            isRunning
              ? "bg-red-600 text-white hover:bg-red-700"
              : "bg-white text-black hover:bg-gray-200"
          }`}
        >
          {isRunning ? "Stop Detection" : "Start Live Detection"}
        </motion.button>

        <label className="px-6 py-3 border border-white/40 rounded-full cursor-pointer hover:bg-white/10 transition-all text-white">
          Upload Image
          <input
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileUpload}
          />
        </label>
      </div>

      {/* Uploaded image section */}
      {uploadedImage && (
        <div className="mt-10 relative inline-block border border-white/10 rounded-xl shadow-lg">
          <img
            src={uploadedImage}
            alt="Uploaded"
            className="rounded-xl max-w-full"
          />
          {uploadedDetections.map((det, i) => {
            const [x1, y1, x2, y2] = det.bbox;
            const color =
              det.label.toLowerCase().includes("no") ||
              det.label.toLowerCase().includes("without")
                ? "red"
                : "green";
            return (
              <div
                key={i}
                className={`absolute border-2 border-${color}-400`}
                style={{
                  top: y1,
                  left: x1,
                  width: x2 - x1,
                  height: y2 - y1,
                }}
              >
                <span
                  className={`absolute top-0 left-0 px-1 text-xs font-bold rounded-br-md ${
                    color === "red"
                      ? "bg-red-500 text-white"
                      : "bg-green-400 text-black"
                  }`}
                >
                  {det.label} ({Math.round(det.confidence * 100)}%)
                </span>
              </div>
            );
          })}
          {loading && (
            <p className="text-gray-400 text-sm absolute bottom-2 right-2 bg-black/50 px-2 py-1 rounded-md">
              Detecting...
            </p>
          )}
        </div>
      )}
    </section>
  );
};

export default HelmetDetect;
