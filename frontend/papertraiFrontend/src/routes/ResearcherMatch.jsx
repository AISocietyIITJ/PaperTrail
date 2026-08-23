import React, { useState } from 'react';
import ResumeUploadZone from '../components/researcher-match/ResumeUploadZone';
import FacultyMatchCard from '../components/researcher-match/FacultyMatchCard';
import SkeletonCard from '../components/shared/SkeletonCard';
import EmptyState from '../components/shared/EmptyState';
import { getFacultyMatches } from '../services/api';
import { Users } from 'lucide-react';
import '../components/researcher-match/researcher-match.css';

export default function ResearcherMatch() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [interests, setInterests] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [matches, setMatches] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);

  const handleMatch = async (e) => {
    e.preventDefault();
    if (!selectedFile && !interests.trim()) return;
    
    setIsLoading(true);
    setHasSearched(true);
    
    try {
      const data = await getFacultyMatches(selectedFile, interests);
      setMatches(data.matches || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="researcher-match-container">
      <div className="match-left-pane">
        <h2>Find Faculty Matches</h2>
        <p style={{ color: 'var(--graphite-600)', fontSize: '0.95rem' }}>
          Upload your resume and describe your interests to find potential advisors with overlapping research areas.
        </p>

        <form className="match-form" onSubmit={handleMatch}>
          <div className="form-group">
            <label>1. Upload Resume</label>
            <ResumeUploadZone 
              selectedFile={selectedFile} 
              onFileSelect={setSelectedFile} 
            />
          </div>

          <div className="form-group">
            <label>2. Research Interests (Optional)</label>
            <textarea 
              className="form-input" 
              placeholder="e.g., I am interested in natural language processing, specifically alignment and reward modeling..."
              value={interests}
              onChange={e => setInterests(e.target.value)}
            />
          </div>

          <button 
            type="submit" 
            className="match-submit-btn"
            disabled={!selectedFile && !interests.trim() || isLoading}
          >
            {isLoading ? 'Analyzing...' : 'Find Matches'}
          </button>
        </form>
      </div>

      <div className="match-right-pane">
        {!hasSearched && (
          <EmptyState 
            icon={Users}
            title="No matches yet"
            description="Upload your resume and enter your interests on the left to discover faculty matches."
          />
        )}

        {isLoading && (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        )}

        {!isLoading && hasSearched && matches.length > 0 && (
          <div className="matches-list">
            {matches.map(match => (
              <FacultyMatchCard key={match.facultyId} match={match} />
            ))}
          </div>
        )}

        {!isLoading && hasSearched && matches.length === 0 && (
          <EmptyState 
            icon={Users}
            title="No strong matches found"
            description="Try adding more detailed research interests or a longer resume."
          />
        )}
      </div>
    </div>
  );
}
