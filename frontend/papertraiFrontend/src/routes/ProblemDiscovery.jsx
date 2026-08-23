import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import QueryInputBar from '../components/shared/QueryInputBar';
import QueryCloudCanvas from '../components/problem-discovery/QueryCloudCanvas';
import PaperDetailDrawer from '../components/shared/PaperDetailDrawer';
import { getProblemCloud } from '../services/api';
import '../components/problem-discovery/problem-discovery.css';

export default function ProblemDiscovery() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  
  // Drawer state
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleSearch = async (query) => {
    setIsLoading(true);
    setHasSearched(true);
    
    try {
      const result = await getProblemCloud(query);
      setData(result);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBubbleClick = (paper) => {
    setSelectedPaper(paper);
    setIsDrawerOpen(true);
  };

  return (
    <div className="problem-discovery-container">
      <QueryInputBar 
        mode="problem" 
        onSubmit={handleSearch} 
        isCentered={!hasSearched} 
      />

      <AnimatePresence>
        {hasSearched && data && (
          <motion.div 
            className="query-bubble-fixed"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: 'spring', bounce: 0.4 }}
          >
            {data.query}
          </motion.div>
        )}
      </AnimatePresence>

      {!isLoading && data && (
        <QueryCloudCanvas data={data} onBubbleClick={handleBubbleClick} />
      )}

      {/* Loading state: skeleton bubbles drifting in (simplified for this iteration) */}
      {isLoading && hasSearched && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: 'var(--graphite-600)' }}>
          Simulating problem space...
        </div>
      )}

      <PaperDetailDrawer 
        isOpen={isDrawerOpen} 
        onClose={() => setIsDrawerOpen(false)}
        paper={selectedPaper}
        edgeInfo={null} // Edge info only relevant in DAG (UC1)
      />
    </div>
  );
}
