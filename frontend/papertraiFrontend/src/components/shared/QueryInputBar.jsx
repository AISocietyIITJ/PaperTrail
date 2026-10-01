import React, { useState, useRef, useEffect } from 'react';
import { Search, ArrowRight, ChevronDown, ChevronUp } from 'lucide-react';
import './query-input-bar.css';

export default function QueryInputBar({ mode = 'path', onSubmit, isCentered = false }) {
  const [query, setQuery] = useState('');
  const [hops, setHops] = useState(2);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      mode === 'path' ? onSubmit(query.trim(), hops) : onSubmit(query.trim());
    }
  };

  const placeholder = mode === 'path' 
    ? "Enter a target domain or topic (e.g. 'Attention mechanisms')..."
    : "Describe the problem you're trying to solve...";

  return (
    <div className={`query-bar-container ${isCentered ? 'centered' : ''}`}>
      <form className="query-form" onSubmit={handleSubmit}>
        {mode !== 'path' && <Search className="query-icon" size={20} />}
        
        {mode === 'path' && (
          <div className="hops-dropdown-container" ref={dropdownRef}>
            <button 
              type="button" 
              className="hops-dropdown-toggle"
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            >
              {hops} {hops === 1 ? 'Hop' : 'Hops'}
              {isDropdownOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
            {isDropdownOpen && (
              <div className="hops-dropdown-menu">
                {[1, 2, 3].map(val => (
                  <div 
                    key={val} 
                    className={`hops-dropdown-item ${hops === val ? 'active' : ''}`}
                    onClick={() => { setHops(val); setIsDropdownOpen(false); }}
                  >
                    {val} {val === 1 ? 'Hop' : 'Hops'}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <input 
          type="text" 
          className={`query-input ${mode === 'path' ? 'with-left-dropdown' : ''}`}
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
