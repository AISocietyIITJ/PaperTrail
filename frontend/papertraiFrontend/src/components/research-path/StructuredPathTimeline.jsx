import React from 'react';
import './StructuredPathTimeline.css';

export default function StructuredPathTimeline({ data, onNodeClick }) {
  const path = data.path || [];

  return (
    <div className="structured-timeline-container">
      {path.map((paper, index) => {
        // Map fields to match what PaperDetailDrawer expects
        const mappedPaper = {
          ...paper,
          publishedDate: paper.year ? new Date(paper.year, 0, 1).toISOString() : new Date().toISOString(),
          authors: [],
          categoryCode: 'CS',
          arxivUrl: `https://arxiv.org/abs/${paper.paperId}`,
          pdfUrl: `https://arxiv.org/pdf/${paper.paperId}.pdf`
        };

        return (
          <div key={paper.paperId || index} className="timeline-item">
            <div className="timeline-step">
              <div className="step-circle">{paper.step}</div>
              {index < path.length - 1 && <div className="step-line"></div>}
            </div>
            <div 
              className="timeline-content paper-node" 
              onClick={() => onNodeClick && onNodeClick(mappedPaper)}
            >
              <div className="node-header">
                <span className="node-year">{paper.year}</span>
                <span className="node-citations">Citations: {paper.citations}</span>
              </div>
              <h3 className="node-title">{paper.title}</h3>
              {paper.abstract && (
                <p className="node-abstract-snippet">
                  {paper.abstract.substring(0, 150)}...
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
