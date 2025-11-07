import React from "react";
import { motion } from "framer-motion";

const About = () => {
  return (
    <section
      id="about"
      className="py-24 px-6 flex flex-col items-center text-center bg-white/5 backdrop-blur-lg rounded-2xl mx-6 mt-20 glass"
    >
      <motion.h2
        className="text-4xl font-bold fancy-text mb-6"
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        About HelmetAI
      </motion.h2>

      <motion.p
        className="max-w-3xl text-gray-300 text-lg leading-relaxed"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.8 }}
      >
         HelmetAI is an AI-powered safety platform designed to protect construction site workers.
        Built with <span className="fancy-text font-semibold">YOLOv8</span> and a FastAPI backend, it performs real-time helmet detection from live cameras or uploaded images.
        The system identifies workers without helmets and instantly triggers alerts — helping site supervisors enforce safety compliance and prevent workplace injuries.
        
      </motion.p>
    </section>
  );
};

export default About;
