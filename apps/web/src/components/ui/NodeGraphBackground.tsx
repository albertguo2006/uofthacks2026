'use client';

import { useEffect, useRef, useCallback } from 'react';

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
}

interface NodeGraphBackgroundProps {
  nodeCount?: number;
  connectionDistance?: number;
  nodeColor?: string;
  edgeColor?: string;
  cursorInfluenceRadius?: number;
  cursorRepelStrength?: number;
  cursorTrailDelay?: number;
}

export default function NodeGraphBackground({
  nodeCount = 100,
  connectionDistance = 150,
  nodeColor = 'rgba(14, 165, 233, 0.8)',
  edgeColor = 'rgba(55, 183, 241, 0.2)',
  cursorInfluenceRadius = 150,
  cursorRepelStrength = 0.25,
  cursorTrailDelay = 0.15,
}: NodeGraphBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const cursorCanvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<Node[]>([]);
  const mouseRef = useRef({ x: -1000, y: -1000 });
  const trailingCursorRef = useRef({ x: -1000, y: -1000 });
  const animationRef = useRef<number>();
  const dimensionsRef = useRef({ width: 0, height: 0 });

  const timeRef = useRef(0);

  const initNodes = useCallback((width: number, height: number) => {
    const nodes: Node[] = [];
    for (let i = 0; i < nodeCount; i++) {
      // Give each node a random angle for its base flow direction
      const angle = Math.random() * Math.PI * 2;
      const speed = 0.2 + Math.random() * 0.3;
      nodes.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        radius: Math.random() * 2 + 1,
      });
    }
    nodesRef.current = nodes;
  }, [nodeCount]);

  const updateNodes = useCallback((width: number, height: number) => {
    const nodes = nodesRef.current;
    const mouse = mouseRef.current;
    const trailingCursor = trailingCursorRef.current;
    timeRef.current += 0.008;
    const time = timeRef.current;

    // Update trailing cursor position with smoother delay (lower = smoother)
    if (mouse.x > 0 && mouse.y > 0) {
      trailingCursor.x += (mouse.x - trailingCursor.x) * cursorTrailDelay;
      trailingCursor.y += (mouse.y - trailingCursor.y) * cursorTrailDelay;
    } else {
      // Smoothly move trailing cursor off screen when mouse leaves
      trailingCursor.x += (-1000 - trailingCursor.x) * cursorTrailDelay;
      trailingCursor.y += (-1000 - trailingCursor.y) * cursorTrailDelay;
    }

    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      
      // Calculate distance to trailing cursor (not actual mouse)
      const dx = node.x - trailingCursor.x;
      const dy = node.y - trailingCursor.y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      // Apply cursor repulsion with more impact
      if (distance < cursorInfluenceRadius && distance > 0) {
        const force = (cursorInfluenceRadius - distance) / cursorInfluenceRadius;
        const angle = Math.atan2(dy, dx);
        node.vx += Math.cos(angle) * force * cursorRepelStrength;
        node.vy += Math.sin(angle) * force * cursorRepelStrength;
      }

      // Add organic flowing movement using sine waves (slower)
      // Each node has a unique phase based on its index
      const phase = i * 0.1;
      const flowX = Math.sin(time + phase) * 0.012;
      const flowY = Math.cos(time * 0.7 + phase) * 0.012;
      node.vx += flowX;
      node.vy += flowY;

      // Add slight random drift for more organic feel
      node.vx += (Math.random() - 0.5) * 0.006;
      node.vy += (Math.random() - 0.5) * 0.006;

      // Apply velocity with gentle damping (keeps momentum longer)
      node.x += node.vx;
      node.y += node.vy;
      node.vx *= 0.99;
      node.vy *= 0.99;

      // Maintain minimum velocity for constant flow (slower)
      const vel = Math.sqrt(node.vx * node.vx + node.vy * node.vy);
      const minVel = 0.15;
      const maxVel = 1.2;
      
      if (vel < minVel) {
        // Boost velocity if too slow
        const angle = Math.atan2(node.vy, node.vx);
        node.vx = Math.cos(angle) * minVel;
        node.vy = Math.sin(angle) * minVel;
      } else if (vel > maxVel) {
        // Cap velocity if too fast
        node.vx = (node.vx / vel) * maxVel;
        node.vy = (node.vy / vel) * maxVel;
      }

      // Wrap around edges smoothly
      if (node.x < -10) node.x = width + 10;
      if (node.x > width + 10) node.x = -10;
      if (node.y < -10) node.y = height + 10;
      if (node.y > height + 10) node.y = -10;
    }
  }, [cursorInfluenceRadius, cursorRepelStrength, cursorTrailDelay]);

  const drawBackground = useCallback((ctx: CanvasRenderingContext2D, width: number, height: number) => {
    const nodes = nodesRef.current;
    const trailingCursor = trailingCursorRef.current;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw edges between nodes
    ctx.strokeStyle = edgeColor;
    ctx.lineWidth = 1.5;

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < connectionDistance) {
          const opacity = 1 - distance / connectionDistance;
          ctx.strokeStyle = edgeColor.replace(/[\d.]+\)$/, `${opacity * 0.3})`);
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.stroke();
        }
      }
    }

    // Draw edges to trailing cursor
    if (trailingCursor.x > 0 && trailingCursor.y > 0) {
      for (const node of nodes) {
        const dx = node.x - trailingCursor.x;
        const dy = node.y - trailingCursor.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < cursorInfluenceRadius) {
          const opacity = 1 - distance / cursorInfluenceRadius;
          ctx.strokeStyle = `rgba(255, 255, 255, ${opacity * 0.4})`;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(node.x, node.y);
          ctx.lineTo(trailingCursor.x, trailingCursor.y);
          ctx.stroke();
        }
      }
    }

    // Draw nodes
    for (const node of nodes) {
      const dx = node.x - trailingCursor.x;
      const dy = node.y - trailingCursor.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      // Nodes glow brighter near trailing cursor
      let glowIntensity = 1;
      if (distance < cursorInfluenceRadius) {
        glowIntensity = 1 + (1 - distance / cursorInfluenceRadius) * 2;
      }

      ctx.fillStyle = nodeColor;
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius * glowIntensity, 0, Math.PI * 2);
      ctx.fill();

      // Add glow effect for nearby nodes
      if (distance < cursorInfluenceRadius) {
        const gradient = ctx.createRadialGradient(
          node.x, node.y, 0,
          node.x, node.y, node.radius * glowIntensity * 3
        );
        gradient.addColorStop(0, `rgba(14, 165, 233, ${0.5 * (1 - distance / cursorInfluenceRadius)})`);
        gradient.addColorStop(1, 'rgba(14, 165, 233, 0)');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius * glowIntensity * 3, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }, [connectionDistance, cursorInfluenceRadius, edgeColor, nodeColor]);

  const drawCursor = useCallback((ctx: CanvasRenderingContext2D, width: number, height: number) => {
    const trailingCursor = trailingCursorRef.current;

    // Clear cursor canvas
    ctx.clearRect(0, 0, width, height);

    // Draw custom trailing cursor (small white circle) - on top layer
    if (trailingCursor.x > 0 && trailingCursor.y > 0) {
      // Outer glow
      const gradient = ctx.createRadialGradient(
        trailingCursor.x, trailingCursor.y, 0,
        trailingCursor.x, trailingCursor.y, 30
      );
      gradient.addColorStop(0, 'rgba(255, 255, 255, 0.3)');
      gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.1)');
      gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(trailingCursor.x, trailingCursor.y, 30, 0, Math.PI * 2);
      ctx.fill();

      // Inner white circle
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.beginPath();
      ctx.arc(trailingCursor.x, trailingCursor.y, 6, 0, Math.PI * 2);
      ctx.fill();

      // White border
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(trailingCursor.x, trailingCursor.y, 10, 0, Math.PI * 2);
      ctx.stroke();
    }
  }, []);

  const animate = useCallback(() => {
    const canvas = canvasRef.current;
    const cursorCanvas = cursorCanvasRef.current;
    if (!canvas || !cursorCanvas) return;

    const ctx = canvas.getContext('2d');
    const cursorCtx = cursorCanvas.getContext('2d');
    if (!ctx || !cursorCtx) return;

    const { width, height } = dimensionsRef.current;
    
    updateNodes(width, height);
    drawBackground(ctx, width, height);
    drawCursor(cursorCtx, width, height);

    animationRef.current = requestAnimationFrame(animate);
  }, [updateNodes, drawBackground, drawCursor]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const cursorCanvas = cursorCanvasRef.current;
    if (!canvas || !cursorCanvas) return;

    const handleResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      canvas.width = width;
      canvas.height = height;
      cursorCanvas.width = width;
      cursorCanvas.height = height;
      dimensionsRef.current = { width, height };

      if (nodesRef.current.length === 0) {
        initNodes(width, height);
      }
    };

    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseLeave = () => {
      mouseRef.current = { x: -1000, y: -1000 };
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length > 0) {
        mouseRef.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      }
    };

    const handleTouchEnd = () => {
      mouseRef.current = { x: -1000, y: -1000 };
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);
    window.addEventListener('touchmove', handleTouchMove);
    window.addEventListener('touchend', handleTouchEnd);

    animate();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('touchend', handleTouchEnd);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [animate, initNodes]);

  return (
    <>
      {/* Background canvas for nodes and edges - behind content */}
      <canvas
        ref={canvasRef}
        className="fixed inset-0 pointer-events-none"
        style={{ zIndex: 0 }}
      />
      {/* Cursor canvas - behind UI elements */}
      <canvas
        ref={cursorCanvasRef}
        className="fixed inset-0 pointer-events-none"
        style={{ zIndex: 1 }}
      />
    </>
  );
}
