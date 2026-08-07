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
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  
  // Set layout algorithm configuration
  // rankdir: LR (Left to Right)
  // align: UL (Up Left) or undefined to let it center nodes naturally within ranks
  // nodesep: vertical spacing between nodes in the same rank
  // ranksep: horizontal spacing between ranks
  dagreGraph.setGraph({ 
    rankdir: 'LR',
    nodesep: 150, 
    ranksep: 350
  });

  nodes.forEach((node) => {
    // Dimensions of our PaperNode component
    dagreGraph.setNode(node.id, { width: 300, height: 120 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 150,
        y: nodeWithPosition.y - 60,
      },
    };
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
