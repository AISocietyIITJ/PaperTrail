import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import './researcher-match.css';

export default function FacultyMatchCard({ match }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const initials = match.name.split(' ').map(n => n[0]).join('').substring(0, 2);

  return (
    <div className="match-card">
      <div className="match-header">
        <div className="match-avatar">{initials}</div>
        <div className="match-title-group">
          <h3 className="match-name">{match.name}</h3>
          <span className="match-dept">{match.department}</span>
        </div>
        <div className="match-score-container">
          <span className="match-score-value">{(match.matchScore * 100).toFixed(0)}%</span>
          <div className="score-bar-bg">
            <div className="score-bar-fill" style={{ width: `${match.matchScore * 100}%` }}></div>
          </div>
        </div>
      </div>

      <p className="match-summary">{match.summary}</p>

      <button 
        className="action-btn" 
        onClick={() => setIsExpanded(!isExpanded)}
        style={{ marginBottom: isExpanded ? '1rem' : '1rem' }}
      >
        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        {isExpanded ? 'Hide Evidence' : 'Show Evidence'}
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="evidence-panel-container"
          >
            <div className="evidence-panel">
              <h4 className="evidence-title">Overlapping Work</h4>
              <div className="evidence-list">
                {match.evidencePapers.map((paper, idx) => (
                  <div key={idx} className="evidence-item">
                    <span className="evidence-paper-title">{paper.title}</span>
                    <div className="evidence-meta">
                      <span className="evidence-year">{paper.year}</span>
                      <span className="evidence-topics">{paper.overlapTopics.join(', ')}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <a href={match.profileUrl} target="_blank" rel="noopener noreferrer" className="match-profile-link">
        View Faculty Profile &rarr;
      </a>
    </div>
  );
}
