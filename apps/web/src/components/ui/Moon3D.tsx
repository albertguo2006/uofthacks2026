'use client';

import { useRef, Suspense, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';

function MoonModel() {
  const meshRef = useRef<THREE.Group>(null);
  const { scene } = useGLTF('/models/moon/scene.gltf');
  
  // Clone the scene to avoid issues with reusing the same object
  const clonedScene = useMemo(() => scene.clone(), [scene]);

  // Slowly rotate the moon on its axis
  useFrame((_, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.05; // Slow rotation speed
    }
  });

  return (
    <group ref={meshRef}>
      <primitive 
        object={clonedScene} 
        scale={6.5} 
        position={[0, -6.5, 0]} // Position so only top half is visible
      />
    </group>
  );
}

export default function Moon3D() {
  return (
    <div 
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 1 }} // Between NodeGraphBackground (z-index: 0) and content (z-index: 10)
    >
      <Canvas
        camera={{ 
          position: [0, 0, 5], 
          fov: 50,
          near: 0.1,
          far: 1000
        }}
        style={{ 
          position: 'absolute',
          bottom: 0,
          left: 0,
          width: '100%',
          height: '60vh', // Only render in bottom portion of screen
        }}
        gl={{ 
          alpha: true, 
          antialias: true,
          powerPreference: 'high-performance'
        }}
      >
        <ambientLight intensity={0.3} />
        <directionalLight 
          position={[5, 5, 5]} 
          intensity={1.2} 
          castShadow 
        />
        <directionalLight 
          position={[-3, 2, -5]} 
          intensity={0.4} 
        />
        <Suspense fallback={null}>
          <MoonModel />
        </Suspense>
      </Canvas>
    </div>
  );
}

// Preload the model
useGLTF.preload('/models/moon/scene.gltf');
