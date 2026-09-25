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

  return (
    <div className="research-path-container">
      <QueryInputBar mode="path" onSubmit={handleSearch} isCentered={!hasSearched} />

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
        <StructuredPathTimeline data={data} onNodeClick={handleNodeClick} />
      )}
      
      {!isLoading && hasSearched && !data && (
        <EmptyState 
          icon={Map}
          title="No path found"
          description="Could not map a connected research path for that topic."
        />
      )}

      <PaperDetailDrawer 
        isOpen={isDrawerOpen} 
        onClose={() => setIsDrawerOpen(false)}
        paper={selectedPaper}
        edgeInfo={drawerEdge}
      />
    </div>
  );
}
