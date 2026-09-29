import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ExternalLink, Download, FileText } from 'lucide-react';
import Badge from './Badge';
import './paper-drawer.css';

function useIsMobile(breakpoint = 600) {
  const [isMobile, setIsMobile] = useState(() => window.innerWidth <= breakpoint);
  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${breakpoint}px)`);
    const handler = (e) => setIsMobile(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [breakpoint]);
  return isMobile;
}

export default function PaperDetailDrawer({ paper, edgeInfo, isOpen, onClose }) {
  const isMobile = useIsMobile(600);
  const [semanticScholarUrl, setSemanticScholarUrl] = useState(null);

  useEffect(() => {
    async function fetchSemanticScholarLink() {
      if (paper && paper.title && isOpen && paper.categoryCode !== 'QUERY') {
        setSemanticScholarUrl(null);
        try {
          const keysStr = import.meta.env.VITE_SEMANTIC_SCHOLAR_API_KEYS || "";
          const keys = keysStr.split(",").filter(k => k.trim().length > 0);
          const headers = {};
          if (keys.length > 0) {
            const key = keys[Math.floor(Math.random() * keys.length)];
            headers['x-api-key'] = key.trim();
          }
          const response = await fetch(`https://api.semanticscholar.org/graph/v1/paper/search?query=${encodeURIComponent(paper.title)}&limit=1&fields=url`, {
            headers
          });
          if (!response.ok) return;
          const data = await response.json();
          if (data && data.data && data.data.length > 0) {
            setSemanticScholarUrl(data.data[0].url);
          }
        } catch (err) {
          console.error("Error fetching Semantic Scholar link", err);
        }
      }
    }
    fetchSemanticScholarLink();
  }, [paper, isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Determine animation direction: slide from right on desktop, slide from bottom on mobile
  const panelVariants = isMobile
    ? { hidden: { y: '100%' }, visible: { y: 0 }, exit: { y: '100%' } }
    : { hidden: { x: '100%' }, visible: { x: 0 }, exit: { x: '100%' } };

  return (
    <AnimatePresence>
      {isOpen && paper && (
        <>
          <motion.div
            className="drawer-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div
            className="drawer-panel"
            variants={panelVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={{ type: 'tween', ease: 'easeOut', duration: 0.28 }}
            role="dialog"
            aria-modal="true"
            aria-label="Paper details"
          >
            <div className="drawer-header">
              <button className="drawer-close" onClick={onClose} aria-label="Close drawer">
                <X size={20} />
              </button>
            </div>

            <div className="drawer-content">
              <div className="drawer-meta-top">
                <span className="drawer-date">{new Date(paper.publishedDate).getFullYear()}</span>
                <Badge label={paper.categoryCode} variant="category" />
              </div>

              <h2 className="drawer-title">{paper.title}</h2>
              <p className="drawer-authors">{paper.authors?.join(', ')}</p>

              {edgeInfo && (
                <div className="drawer-edge-info">
                  <span className="edge-info-label">Connection:</span>
                  <Badge label={edgeInfo.reason} variant={edgeInfo.reason} />
                  <span className="edge-score">
                    Sim: {edgeInfo.similarity != null ? Number(edgeInfo.similarity).toFixed(2) : 'N/A'}
                  </span>
                </div>
              )}

              <div className="drawer-section">
                <h3>Abstract</h3>
                <p className="drawer-abstract">{paper.abstract}</p>
              </div>

              {paper.categoryCode !== 'QUERY' && (
                <div className="drawer-actions">
                  <a href={paper.arxivUrl} target="_blank" rel="noopener noreferrer" className="action-btn">
                    <ExternalLink size={16} />
                    arXiv Page
                  </a>
                  <a href={paper.pdfUrl} target="_blank" rel="noopener noreferrer" className="action-btn primary">
                    <Download size={16} />
                    Open PDF
                  </a>
                  {semanticScholarUrl && (
                    <a href={semanticScholarUrl} target="_blank" rel="noopener noreferrer" className="action-btn">
                      <ExternalLink size={16} />
                      Semantic Scholar
                    </a>
                  )}
                  <button
                    className="action-btn"
                    onClick={() => navigator.clipboard.writeText(
                      `@article{${paper.arxivId}, title={${paper.title}}, author={${paper.authors?.join(' and ')}}, year={${new Date(paper.publishedDate).getFullYear()}}}`
                    )}
                  >
                    <FileText size={16} />
                    Copy BibTeX
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
