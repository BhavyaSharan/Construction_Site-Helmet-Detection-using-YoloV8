import React, { useState } from "react";
import { Menu, X } from "lucide-react";
import { motion } from "framer-motion";

const Navbar = () => {
  const [menuOpen, setMenuOpen] = useState(false);

  const toggleMenu = () => setMenuOpen(!menuOpen);

  // Smooth scroll function
  const handleScroll = (id) => {
    const section = document.getElementById(id);
    if (section) {
      section.scrollIntoView({ behavior: "smooth" });
      setMenuOpen(false); // close mobile menu after click
    }
  };

  return (
    <nav className="fixed top-4 left-1/2 -translate-x-1/2 z-50 w-[90%] md:w-[80%] bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl shadow-lg glass">
      <div className="flex items-center justify-between px-6 py-3">
        {/* Logo */}
        <motion.h1
          whileHover={{ scale: 1.05 }}
          className="text-xl font-semibold fancy-text cursor-pointer"
          onClick={() => handleScroll("hero")}
        >
          Helmet<span className="text-white">AI</span>
        </motion.h1>

        {/* Desktop Nav Links */}
        <div className="hidden md:flex items-center gap-10">
          <motion.button
            whileHover={{ scale: 1.1 }}
            onClick={() => handleScroll("detect")}
            className="text-white font-medium fancy-text text-lg"
          >
            Detect
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.1 }}
            onClick={() => handleScroll("about")}
            className="text-white font-medium fancy-text text-lg"
          >
            About
          </motion.button>

          
        </div>

        {/* Mobile Menu Toggle */}
        <div className="md:hidden">
          <button onClick={toggleMenu} className="text-white focus:outline-none">
            {menuOpen ? <X size={28} /> : <Menu size={28} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {menuOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="md:hidden flex flex-col items-center gap-4 pb-4 border-t border-white/10"
        >
          <button
            onClick={() => handleScroll("detect")}
            className="text-white text-lg fancy-text"
          >
            Detect
          </button>
          <button
            onClick={() => handleScroll("about")}
            className="text-white text-lg fancy-text"
          >
            About
          </button>
         
        </motion.div>
      )}
    </nav>
  );
};

export default Navbar;
