import React, { useCallback } from "react";
import Particles from "react-tsparticles";
import { loadSlim } from "@tsparticles/slim";

const Background = () => {
  const particlesInit = useCallback(async (engine) => {
    await loadSlim(engine);
  }, []);

  return (
    <Particles
      id="tsparticles"
      init={particlesInit}
      className="fixed inset-0 -z-50"
      options={{
        background: { color: "#000000" },
        fpsLimit: 60,
        interactivity: {
          events: {
            onHover: { enable: true, mode: "repulse" },
            onClick: { enable: true, mode: "push" },
          },
          modes: {
            repulse: { distance: 120 },
            push: { quantity: 2 },
          },
        },
        particles: {
  color: { value: ["#00ffff", "#ff00ff"] },
  links: { color: "#00ffff", distance: 150, enable: true, opacity: 0.6, width: 1 },

          move: {
            enable: true,
            speed: 0.6,
            outModes: { default: "bounce" },
          },
          number: { value: 50 },
          opacity: { value: 0.2 },
          shape: { type: "circle" },
          size: { value: { min: 1, max: 4 } },
        },
        detectRetina: true,
      }}
    />
  );
};

export default Background;
