import Background from "./components/Background";
import React from "react";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import HelmetDetect from "./components/HelmetDetect";
import About from "./components/About";

import CustomCursor from "./components/CustomCursor"; // 👈 added import

function App() {
  return (
    <div className="overflow-x-hidden scroll-smooth relative">
      {/* Glowing Custom Cursor */}
      <CustomCursor />

      {/* Background Particles */}
      <Background />

      {/* Main Website Content */}
      <Navbar />
      <Hero />
      <HelmetDetect />
      <About />
      

      <footer className="text-center py-10 text-gray-400 border-t border-white/10 mt-20 relative z-10">
        <p>
          © {new Date().getFullYear()}{" "}
          <span className="fancy-text">HelmetAI</span> Created by 
          Team 05
        </p>
      </footer>
    </div>
  );
}

export default App;
