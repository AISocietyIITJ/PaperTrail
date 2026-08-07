import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3-force';
import PaperBubble from './PaperBubble';
import './problem-discovery.css';

export default function QueryCloudCanvas({ data, onBubbleClick }) {
  const containerRef = useRef(null);
  const [nodes, setNodes] = useState([]);

  useEffect(() => {
    if (!data || !containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;
    
    // Check for prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Create physics nodes
    const simNodes = data.papers.map(p => ({
      ...p,
      // Start in a random cluster in the center so radial forces pull them out
      x: width / 2 + (Math.random() - 0.5) * 10,
      y: height / 2 + (Math.random() - 0.5) * 10,
      // Base radius of the paper bubble (140px width = 70px radius) + padding
      radius: 80 
    }));

    // The maximum orbital distance from the center (query)
    const maxOrbitDistance = Math.min(width, height) / 2.5;

    const simulation = d3.forceSimulation(simNodes)
      // Force Radial: closer similarity (high relevance) = smaller radius (closer to center)
      .force('radial', d3.forceRadial(
        d => (1 - d.relevance) * maxOrbitDistance + 200, // Add 200px offset to strictly leave room for the center Query bubble (radius 100)
        width / 2, 
        height / 2
      ).strength(1.5))
      // Strong Collision force to strictly prevent overlapping
      .force('collide', d3.forceCollide().radius(d => d.radius).iterations(4).strength(1))
      // Mild repulsion to spread out if they are on the same orbit
      .force('charge', d3.forceManyBody().strength(-200))
      // Center gravity to keep the cluster centered if window resizes
      .force('center', d3.forceCenter(width / 2, height / 2).strength(0.05));

    // Tick handler
    simulation.on('tick', () => {
      // Small random drift if not reduced motion, applying tiny forces
      if (!prefersReducedMotion && simulation.alpha() < 0.1) {
        simNodes.forEach(node => {
          node.vx += (Math.random() - 0.5) * 0.2;
          node.vy += (Math.random() - 0.5) * 0.2;
        });
      }
      
      // Keep within bounds
      simNodes.forEach(node => {
        node.x = Math.max(node.radius, Math.min(width - node.radius, node.x));
        node.y = Math.max(node.radius, Math.min(height - node.radius, node.y));
      });
      
      setNodes([...simNodes]);
    });

    return () => {
      simulation.stop();
    };
  }, [data]);

  return (
    <div className="cloud-canvas-container" ref={containerRef}>
      {nodes.map(node => (
        <PaperBubble 
          key={node.nodeIdx}
          paper={node}
          onClick={onBubbleClick}
          style={{
            left: `${node.x}px`,
            top: `${node.y}px`
          }}
        />
      ))}
    </div>
  );
}
