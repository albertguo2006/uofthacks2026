'use client';

import { useEffect, useRef } from 'react';

//no lnger used to minimize lag :(

export default function GrainOverlay() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: -1000, y: -1000 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let lastTime = 0;
    const fps = 8; // Very slow refresh rate
    const frameInterval = 1000 / fps;
    const grainSize = 1; // Size of each grain in pixels
    const spacing = 1000; // Space between grains (larger = more spaced out)
    const mouseInfluenceRadius = 100; // How far the mouse affects grains

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    const generateNoise = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const mouse = mouseRef.current;
      
      // Generate larger, more spaced out grain blocks
      for (let x = 0; x < canvas.width; x += spacing) {
        for (let y = 0; y < canvas.height; y += spacing) {
          // Only draw some grains randomly for more sparse effect
          if (Math.random() > 0.5) continue;
          
          // Calculate distance from mouse
          const dx = x - mouse.x;
          const dy = y - mouse.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          // Grains near mouse are brighter and larger
          let alpha = 0.4;
          let size = grainSize;
          
          if (distance < mouseInfluenceRadius) {
            const influence = 1 - (distance / mouseInfluenceRadius);
            alpha = Math.max(0,0.4 - (influence*0.5)); // Up to 0.37 opacity near mouse
          }
          
          const value = Math.floor(Math.random() * 256);
          ctx.fillStyle = `rgba(${value}, ${value}, ${value}, ${alpha})`;
          ctx.fillRect(x - size/2, y - size/2, size, size);
        }
      }
    };

    const animate = (currentTime: number) => {
      animationId = requestAnimationFrame(animate);

      const elapsed = currentTime - lastTime;
      if (elapsed < frameInterval) return;

      lastTime = currentTime - (elapsed % frameInterval);
      generateNoise();
    };

    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseLeave = () => {
      mouseRef.current = { x: -1000, y: -1000 };
    };

    resize();
    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);
    animationId = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
      cancelAnimationFrame(animationId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ 
        zIndex: -1, // Behind all other elements
        mixBlendMode: 'overlay',
      }}
    />
  );
}
