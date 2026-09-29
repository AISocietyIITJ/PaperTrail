import React, { useState } from 'react';
import QueryInputBar from '../components/shared/QueryInputBar';
import StructuredPathTimeline from '../components/research-path/StructuredPathTimeline';
import PaperDetailDrawer from '../components/shared/PaperDetailDrawer';
import EmptyState from '../components/shared/EmptyState';
import { getStructuredPath } from '../services/api';
import { Map } from 'lucide-react';
import '../components/research-path/research-path.css';

export default function ResearchPath() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  
  // Drawer state
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [drawerEdge, setDrawerEdge] = useState(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleSearch = async (query) => {
    setIsLoading(true);
    setHasSearched(true);
    
    try {
      const result = await getStructuredPath(query);
      setData(result);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNodeClick = (paper) => {
    setSelectedPaper(paper);
    setDrawerEdge(null); // No edge info needed for simple vertical timeline
    
    setIsDrawerOpen(true);
  };

  const handleEdgeClick = (edgeData) => {
    // We need to find the target paper to show in the drawer, or we can just show the edge info
    // The edgeData represents the prerequisite relation. We can show it in the drawer alongside the target paper,
    // or just pass a dummy paper so the drawer opens and shows the edge info.
    // Let's find the paper that is the target of this edge (or source) if we want to show it.
    // Assuming `edgeData` has { paperId, title, reason, similarity } from prerequisite list
    setDrawerEdge(edgeData);
    // Find the paper that this prerequisite points to? Actually, edgeData is the prerequisite.
    const targetPaper = data?.path?.find(p => p.paperId === edgeData.paperId);
    if (targetPaper) {
      setSelectedPaper(targetPaper);
    } else {
      setSelectedPaper({
        title: edgeData.title,
        publishedDate: new Date().toISOString(),
        abstract: "This is a prerequisite paper.",
        authors: []
      });
    }
    setIsDrawerOpen(true);
  };

  return (
    <div className="research-path-container">
      <QueryInputBar mode="path" onSubmit={handleSearch} isCentered={!hasSearched} />

      <div className="research-path-scroll">
        {!hasSearched && (
          <div style={{ flex: 1 }}>
            {/* Input bar is centered, no empty state needed per implementation plan */}
          </div>
        )}

        {isLoading && hasSearched && (
          <EmptyState 
            icon={Map}
            title="Mapping Route..."
            description="Traversing the citation graph to find foundational papers."
          />
        )}

        {!isLoading && data && (
          <StructuredPathTimeline data={data} onNodeClick={handleNodeClick} onEdgeClick={handleEdgeClick} />
        )}
        
        {!isLoading && hasSearched && !data && (
          <EmptyState 
            icon={Map}
            title="No path found"
            description="Could not map a connected research path for that topic."
          />
        )}
      </div>

      <PaperDetailDrawer 
        isOpen={isDrawerOpen} 
        onClose={() => setIsDrawerOpen(false)}
        paper={selectedPaper}
        edgeInfo={drawerEdge}
      />
    </div>
  );
}
