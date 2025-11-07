import React from "react";
import { motion } from "framer-motion";

const Hero = () => {
  return (
    <section
      id="hero"
      className="relative flex flex-col items-center justify-center text-center px-4 py-32 md:py-44 overflow-hidden"
    >
      {/* Animated gradient background */}
      <motion.div
        className="absolute inset-0 -z-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 2 }}
      >
        <div className="absolute w-[600px] h-[600px] bg-[#5B8EFF]/30 blur-[150px] rounded-full top-10 left-1/3 -translate-x-1/2"></div>
        <div className="absolute w-[500px] h-[500px] bg-[#9F6BFF]/20 blur-[180px] rounded-full bottom-0 right-1/3 translate-x-1/2"></div>
      </motion.div>

      {/* Headline */}
      <motion.h1
        className="text-4xl md:text-6xl font-bold fancy-text leading-tight"
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 1 }}
      >
        Smarter Worksites with  <br /> Real-Time Helmet Detection
      </motion.h1>

      {/* Subheadline */}
      <motion.p
        className="mt-4 text-gray-300 text-lg md:text-xl max-w-2xl"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4, duration: 1 }}
      >
        An AI-powered solution to detect helmet violations and improve workers safety,
        built with deep learning and computer vision.
      </motion.p>

      {/* CTA Buttons */}
      <motion.div
        className="mt-8 flex flex-col md:flex-row gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8, duration: 1 }}
      >
        <a
          href="#detect"
          className="px-6 py-3 bg-white text-black font-semibold rounded-full shadow-md hover:bg-gray-200 transition-all"
        >
          Try Demo
        </a>
        <a
          href="#about"
          className="px-6 py-3 border border-white/40 text-white rounded-full hover:bg-white/10 transition-all"
        >
          Learn More
        </a>
      </motion.div>
    </section>
  );
};

export default Hero;
