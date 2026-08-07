import React from 'react';
import './problem-discovery.css';

export default function PaperBubble({ paper, style, onClick }) {
  // Use a slightly varied scale based on relevance, but keep mostly uniform 
  // as per implementation guide (primary encoding is distance, secondary is slight size variation)
  const scale = 0.85 + (paper.relevance * 0.3);
  
  return (
    <button 
      className="paper-bubble"
      style={{
        ...style,
        transform: `translate(-50%, -50%) scale(${scale})`
      }}
      onClick={() => onClick(paper)}
      title={paper.title}
    >
      <span className="bubble-title">{paper.title}</span>
    </button>
  );
}
