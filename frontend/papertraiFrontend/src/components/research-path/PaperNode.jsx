import React from 'react';
import { Handle, Position } from '@xyflow/react';
import Badge from '../shared/Badge';
import './research-path.css';

export default function PaperNode({ data }) {
  const { paper, isTarget } = data;
  const year = new Date(paper.publishedDate).getFullYear();

  return (
    <div className={`paper-node ${isTarget ? 'target' : ''}`} title={paper.title}>
      <Handle type="target" position={Position.Left} isConnectable={false} />
      
      <div className="node-header">
        <span className="node-year">{year}</span>
        <Badge label={paper.categoryCode} variant="category" />
      </div>
      
      <h3 className="node-title">{paper.title}</h3>

      <Handle type="source" position={Position.Right} isConnectable={false} />
    </div>
  );
}
