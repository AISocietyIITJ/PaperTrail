import React from 'react';
import './skeleton.css';

export default function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton-header">
        <div className="skeleton-avatar"></div>
        <div className="skeleton-title-group">
          <div className="skeleton-line title"></div>
          <div className="skeleton-line subtitle"></div>
        </div>
      </div>
      <div className="skeleton-body">
        <div className="skeleton-line full"></div>
        <div className="skeleton-line full"></div>
        <div className="skeleton-line half"></div>
      </div>
    </div>
  );
}
