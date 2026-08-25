import React, { useMemo } from 'react';
import { ReactFlow, Controls, Background, MiniMap } from '@xyflow/react';
import dagre from 'dagre';
import '@xyflow/react/dist/style.css';
import PaperNode from './PaperNode';
import './research-path.css';

const nodeTypes = {
  paper: PaperNode
};

const getLayoutedElements = (nodes, edges) => {
  // 1. Extract year for each node and group by year
  const nodesByYear = {};
  nodes.forEach(node => {
    const dateStr = node.data.paper.publishedDate;
    const year = dateStr ? new Date(dateStr).getFullYear() : 2020;
    if (!nodesByYear[year]) {
      nodesByYear[year] = [];
    }
    nodesByYear[year].push(node);
  });

  // 2. Sort unique years ascending (oldest on left, newest on right)
  const sortedYears = Object.keys(nodesByYear).sort((a, b) => parseInt(a) - parseInt(b));

  // 3. Position nodes based on year index (X) and stack position (Y)
  const layoutedNodes = [];
  const X_SPACING = 400; // Horizontal distance between years
  const Y_SPACING = 180; // Vertical distance between papers in same year

  sortedYears.forEach((year, yearIndex) => {
    // Within the same year, sort by hopDistance ascending (closest to target at the top)
    // Target is hop 0, so it will be at the top of its year column
    const nodesInYear = nodesByYear[year];
    nodesInYear.sort((a, b) => (a.data.paper.hopDistance || 0) - (b.data.paper.hopDistance || 0));

    nodesInYear.forEach((node, stackIndex) => {
      layoutedNodes.push({
        ...node,
        position: {
          x: yearIndex * X_SPACING,
          y: stackIndex * Y_SPACING,
        },
      });
    });
  });

  return { nodes: layoutedNodes, edges };
};

export default function PathGraphCanvas({ data, onNodeClick }) {
  const { nodes: initialNodes, edges: initialEdges, targetNodeIdx } = data;

  const { nodes, edges } = useMemo(() => {
    // Map backend data to React Flow elements
    const rfNodes = initialNodes.map(n => ({
      id: String(n.nodeIdx),
      type: 'paper',
      data: { paper: n, isTarget: n.nodeIdx === targetNodeIdx },
    }));

    const rfEdges = initialEdges.map(e => {
      // Find destination node to determine hop distance (for styling)
      const dstNode = initialNodes.find(n => n.nodeIdx === e.dst);
      const hopDist = dstNode ? dstNode.hopDistance : 3;
      
      // Calculate opacity and stroke width based on hop distance (0 is closest/target)
      // Hop 0 = opacity 1, stroke 3
      // Hop 1 = opacity 0.7, stroke 2
      // Hop 2+ = opacity 0.4, stroke 1.5
      const opacity = Math.max(0.2, 1 - (hopDist * 0.25));
      const strokeWidth = Math.max(1, 3 - (hopDist * 0.5));

      return {
        id: `e${e.src}-${e.dst}`,
        source: String(e.src),
        target: String(e.dst),
        animated: true,
        style: { 
          stroke: `rgba(99, 102, 241, ${opacity})`, // New route-blue
          strokeWidth,
        },
        markerEnd: {
          type: 'arrowclosed',
          color: `rgba(99, 102, 241, ${opacity})`,
        },
        data: {
          reason: e.reason,
          similarity: e.similarity
        }
      };
    });

    return getLayoutedElements(rfNodes, rfEdges);
  }, [initialNodes, initialEdges, targetNodeIdx]);

  return (
    <div className="graph-canvas-container">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => onNodeClick(node.data.paper)}
        fitView
        attributionPosition="bottom-right"
        colorMode="dark"
      >
        <Controls />
        <MiniMap 
          nodeColor="var(--route-blue)"
          maskColor="rgba(42, 36, 33, 0.7)"
          style={{ backgroundColor: 'var(--surface-color)' }}
        />
        <Background color="var(--graphite-600)" gap={16} />
      </ReactFlow>
    </div>
  );
}
