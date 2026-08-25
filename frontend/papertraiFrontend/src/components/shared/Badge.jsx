import React from 'react';
import './badge.css';

// variant can be: 'category', 'temporal', 'generality', 'score', 'default'
export default function Badge({ label, variant = 'default' }) {
  return (
    <span className={`badge badge-${variant}`}>
      {label}
    </span>
  );
}
