import React, { useState } from 'react';
import { Search, ArrowRight } from 'lucide-react';
import './query-input-bar.css';

export default function QueryInputBar({ mode = 'path', onSubmit, isCentered = false }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSubmit(query.trim());
    }
  };

  const placeholder = mode === 'path' 
    ? "Enter a target domain or topic (e.g. 'Attention mechanisms')..."
    : "Describe the problem you're trying to solve...";

  return (
    <div className={`query-bar-container ${isCentered ? 'centered' : ''}`}>
      <form className="query-form" onSubmit={handleSubmit}>
        <Search className="query-icon" size={20} />
        <input 
          type="text" 
          className="query-input" 
          placeholder={placeholder}
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
        <button type="submit" className="query-submit" disabled={!query.trim()}>
          {mode === 'path' ? 'Map Path' : 'Discover'}
          <ArrowRight size={16} />
        </button>
      </form>
    </div>
  );
}
