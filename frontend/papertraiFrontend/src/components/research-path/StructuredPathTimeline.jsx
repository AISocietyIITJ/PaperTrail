import React, { useMemo, useEffect, useState, useRef } from 'react';
import './StructuredPathTimeline.css';

export default function StructuredPathTimeline({ data, onNodeClick, onEdgeClick }) {
  const path = data.path || [];
  const containerRef = useRef(null);
  const [edges, setEdges] = useState([]);

  // Group papers by level (depth in the DAG)
  const { levels, allPrereqs } = useMemo(() => {
    const depths = {};
    const nodes = {};
    const prereqsList = [];
    
    // First pass: index nodes
    path.forEach(paper => {
      nodes[paper.paperId] = paper;
    });

    // Compute depth
    path.forEach(paper => {
      let maxDepth = -1;
      if (paper.prerequisites && paper.prerequisites.length > 0) {
        paper.prerequisites.forEach(prereq => {
          prereqsList.push({ source: prereq.paperId, target: paper.paperId });
          const d = depths[prereq.paperId];
          if (d !== undefined && d > maxDepth) {
            maxDepth = d;
          }
        });
      }
      depths[paper.paperId] = maxDepth + 1;
    });

    const levelGroups = [];
    path.forEach(paper => {
      const d = depths[paper.paperId];
      if (d === undefined) return;
      if (!levelGroups[d]) levelGroups[d] = [];
      levelGroups[d].push(paper);
    });

    return { levels: levelGroups, nodesById: nodes, allPrereqs: prereqsList };
  }, [path]);

  useEffect(() => {
    const drawEdges = () => {
      if (!containerRef.current) return;
      
      const containerRect = containerRef.current.getBoundingClientRect();
      const newEdges = [];

      allPrereqs.forEach(({ source, target }) => {
        const sourceEl = document.getElementById(`node-${source}`);
        const targetEl = document.getElementById(`node-${target}`);

        if (sourceEl && targetEl) {
          const sourceRect = sourceEl.getBoundingClientRect();
          const targetRect = targetEl.getBoundingClientRect();

          // Calculate center points relative to container
          const startX = sourceRect.left + sourceRect.width / 2 - containerRect.left;
          const startY = sourceRect.bottom - containerRect.top; // Bottom of source
          
          const endX = targetRect.left + targetRect.width / 2 - containerRect.left;
          const endY = targetRect.top - containerRect.top; // Top of target

          newEdges.push({
            id: `${source}-${target}`,
            source,
            target,
            startX,
            startY,
            endX,
            endY
          });
        }
      });
      setEdges(newEdges);
    };

    // Draw initially and on window resize
    drawEdges();
    window.addEventListener('resize', drawEdges);
    // Add a slight delay to ensure DOM is fully rendered (images, fonts, etc)
    const timeout = setTimeout(drawEdges, 100);
    
    return () => {
      window.removeEventListener('resize', drawEdges);
      clearTimeout(timeout);
    };
  }, [allPrereqs, levels]);

  return (
    <div 
      className="structured-timeline-container dag-container" 
      style={{ 
        maxWidth: '1200px', 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '4rem', // increased gap to give lines more room to route cleanly
        position: 'relative', 
        width: '100%', 
        margin: '0 auto',
        padding: '2rem 1rem'
      }}
      ref={containerRef}
    >
      {/* SVG overlay for edges */}
      <svg 
        style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none', zIndex: 0 }}
      >
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="var(--route-blue, #64ffda)" />
          </marker>
        </defs>
        {edges.map((edge) => {
          // Use a clean step (orthogonal) path instead of a web-like bezier curve
          const midY = (edge.startY + edge.endY) / 2;
          // M = move to start, V = vertical line down, H = horizontal line across, V = vertical line down to target
          const d = `M ${edge.startX} ${edge.startY} V ${midY} H ${edge.endX} V ${edge.endY}`;

          return (
            <path
              key={edge.id}
              d={d}
              stroke="var(--route-blue, #64ffda)"
              strokeWidth="2"
              fill="none"
              markerEnd="url(#arrowhead)"
              style={{ opacity: 0.4, cursor: 'pointer', transition: 'all 0.2s', pointerEvents: 'auto' }}
              onMouseEnter={(e) => { e.currentTarget.style.strokeWidth = '4'; e.currentTarget.style.opacity = '1'; }}
              onMouseLeave={(e) => { e.currentTarget.style.strokeWidth = '2'; e.currentTarget.style.opacity = '0.4'; }}
              onClick={() => {
                if (onEdgeClick) {
                  const targetPaperData = path.find(p => p.paperId === edge.target);
                  const prereqData = targetPaperData?.prerequisites?.find(p => p.paperId === edge.source);
                  if (prereqData) {
                    onEdgeClick(prereqData);
                  }
                }
              }}
            />
          );
        })}
      </svg>

      {levels.map((level, depth) => (
        <div key={depth} className="dag-level" style={{ display: 'flex', gap: '3rem', justifyContent: 'center', flexWrap: 'wrap', position: 'relative', zIndex: 1 }}>
          {level.map(paper => {
            const mappedPaper = {
              ...paper,
              publishedDate: paper.year ? new Date(paper.year, 0, 1).toISOString() : new Date().toISOString(),
              authors: [],
              categoryCode: 'CS',
              arxivUrl: `https://arxiv.org/abs/${paper.paperId}`,
              pdfUrl: `https://arxiv.org/pdf/${paper.paperId}.pdf`
            };

            return (
              <div 
                id={`node-${paper.paperId}`}
                key={paper.paperId} 
                className="timeline-content paper-node" 
                onClick={() => onNodeClick && onNodeClick(mappedPaper)}
                style={{ width: '320px', display: 'flex', flexDirection: 'column', background: 'var(--surface-raised, #1a1a1a)', margin: 0 }}
              >
                <div className="node-header">
                  <span className="node-year">{paper.year || 'N/A'}</span>
                  <span className="node-citations">Citations: {paper.citations || 0}</span>
                </div>
                <h3 className="node-title">{paper.title}</h3>
                {paper.abstract && (
                  <p className="node-abstract-snippet">
                    {paper.abstract.substring(0, 150)}...
                  </p>
                )}
                {/* 
                  Keeping prerequisites listed briefly provides context 
                  without them being purely reliant on the visual lines 
                */}
                {paper.prerequisites && paper.prerequisites.length > 0 && (
                  <div style={{ marginTop: 'auto', paddingTop: '10px', fontSize: '0.85em', color: 'var(--graphite-500)', borderTop: '1px solid var(--border-color)' }}>
                    <strong>Builds upon:</strong>
                    <ul style={{ paddingLeft: '15px', margin: '5px 0 0 0', listStyleType: 'circle' }}>
                      {paper.prerequisites.map(p => (
                        <li key={p.paperId}>{p.title}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
