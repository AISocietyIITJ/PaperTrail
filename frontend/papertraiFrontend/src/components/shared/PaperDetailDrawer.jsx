import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ExternalLink, Download, FileText } from 'lucide-react';
import Badge from './Badge';
import './paper-drawer.css';

export default function PaperDetailDrawer({ paper, edgeInfo, isOpen, onClose }) {
  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

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
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'tween', ease: 'easeOut', duration: 0.28 }}
            role="dialog"
            aria-modal="true"
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
                    Sim: {edgeInfo.similarity.toFixed(2)}
                  </span>
                </div>
              )}

              <div className="drawer-section">
                <h3>Abstract</h3>
                <p className="drawer-abstract">{paper.abstract}</p>
              </div>

              <div className="drawer-actions">
                <a href={paper.arxivUrl} target="_blank" rel="noopener noreferrer" className="action-btn">
                  <ExternalLink size={16} />
                  arXiv Page
                </a>
                <a href={paper.pdfUrl} target="_blank" rel="noopener noreferrer" className="action-btn primary">
                  <Download size={16} />
                  Open PDF
                </a>
                <button className="action-btn" onClick={() => navigator.clipboard.writeText(`@article{${paper.arxivId}, title={${paper.title}}, author={${paper.authors?.join(' and ')}}, year={${new Date(paper.publishedDate).getFullYear()}}}`)}>
                  <FileText size={16} />
                  Copy BibTeX
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
