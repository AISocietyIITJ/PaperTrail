import React, { useMemo, useCallback, useEffect } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  MarkerType,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import './StructuredPathTimeline.css';

const nodeWidth = 320;
const nodeHeight = 250;

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  
  dagreGraph.setGraph({ rankdir: direction, nodesep: 150, ranksep: 100 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const newNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    const newNode = {
      ...node,
      targetPosition: 'top',
      sourcePosition: 'bottom',
      // Shift position since react flow nodes anchor to top left, dagre to center
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };

    return newNode;
  });

  return { nodes: newNodes, edges };
};

const PaperNode = ({ data }) => {
  const { paper, onNodeClick } = data;
  
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
      className="timeline-content paper-node" 
      onClick={() => onNodeClick && onNodeClick(mappedPaper)}
      style={{ 
        width: `${nodeWidth}px`, 
        display: 'flex', 
        flexDirection: 'column', 
        background: 'var(--surface-raised, #1a1a1a)', 
        margin: 0,
        cursor: 'pointer'
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: 'var(--route-blue, #64ffda)' }} />
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
      {paper.prerequisites && paper.prerequisites.length > 0 && (
        <div style={{ marginTop: '12px', paddingTop: '10px', fontSize: '0.85em', color: 'var(--graphite-500)', borderTop: '1px solid var(--border-color)' }}>
          <strong>Builds upon:</strong>
          <ul style={{ paddingLeft: '15px', margin: '5px 0 0 0', listStyleType: 'circle' }}>
            {paper.prerequisites.map(p => (
              <li key={p.paperId}>{p.title}</li>
            ))}
          </ul>
        </div>
      )}
      <Handle type="source" position={Position.Bottom} style={{ background: 'var(--route-blue, #64ffda)' }} />
    </div>
  );
};

const nodeTypes = {
  paperNode: PaperNode,
};

function StructuredPathTimelineFlow({ data, onNodeClick, onEdgeClick }) {
  const path = data.path || [];
  const { fitView } = useReactFlow();

  const { initialNodes, initialEdges } = useMemo(() => {
    const nodes = [];
    const edges = [];

    path.forEach(paper => {
      nodes.push({
        id: paper.paperId.toString(),
        type: 'paperNode',
        data: { paper, onNodeClick },
        position: { x: 0, y: 0 },
      });

      if (paper.prerequisites && paper.prerequisites.length > 0) {
        paper.prerequisites.forEach(prereq => {
          edges.push({
            id: `${prereq.paperId}-${paper.paperId}`,
            source: prereq.paperId.toString(),
            target: paper.paperId.toString(),
            type: 'smoothstep', 
            animated: true,
            style: { stroke: 'var(--route-blue, #64ffda)', strokeWidth: 2 },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: 'var(--route-blue, #64ffda)',
            },
            data: {
              sourceData: prereq,
              targetData: paper
            }
          });
        });
      }
    });

    const layouted = getLayoutedElements(nodes, edges);
    return { initialNodes: layouted.nodes, initialEdges: layouted.edges };
  }, [path, onNodeClick]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
    
    // Fit view after a small timeout to let the graph render
    setTimeout(() => {
        fitView({ padding: 0.2 });
    }, 50);
  }, [initialNodes, initialEdges, fitView, setNodes, setEdges]);

  const onEdgeClickInternal = useCallback((event, edge) => {
    if (onEdgeClick && edge.data && edge.data.sourceData) {
      onEdgeClick(edge.data.sourceData);
    }
  }, [onEdgeClick]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      onEdgeClick={onEdgeClickInternal}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      attributionPosition="bottom-left"
      minZoom={0.1}
      maxZoom={2}
    >
      <Controls />
      <MiniMap 
        nodeColor={(node) => 'var(--route-blue, #64ffda)'}
        maskColor="rgba(0, 0, 0, 0.7)"
        style={{ backgroundColor: 'var(--surface-base, #121212)' }}
      />
      <Background color="var(--graphite-600, #444)" gap={16} />
    </ReactFlow>
  );
}

export default function StructuredPathTimeline(props) {
  return (
    <div style={{ width: '100%', height: '100%', minHeight: '600px', display: 'flex', flex: 1 }}>
      <ReactFlowProvider>
        <StructuredPathTimelineFlow {...props} />
      </ReactFlowProvider>
    </div>
  );
}
