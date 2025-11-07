import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";

const CustomCursor = () => {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const moveCursor = (e) => {
      setPosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener("mousemove", moveCursor);
    return () => window.removeEventListener("mousemove", moveCursor);
  }, []);

  return (
    <motion.div
      className="fixed top-0 left-0 w-10 h-10 rounded-full pointer-events-none z-[9999]"
      style={{
        background:
          "radial-gradient(circle, rgba(139,233,253,0.4) 0%, rgba(139,233,253,0.0) 70%)",
        mixBlendMode: "difference",
      }}
      animate={{
        x: position.x - 20,
        y: position.y - 20,
      }}
      transition={{
        type: "spring",
        stiffness: 200,
        damping: 15,
        mass: 0.2,
      }}
    />
  );
};

export default CustomCursor;
