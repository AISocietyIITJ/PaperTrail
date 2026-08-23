import React from 'react';
import { AlertCircle } from 'lucide-react';
import './empty-state.css';

export default function EmptyState({ title, description, icon: Icon = AlertCircle }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">
        <Icon size={48} strokeWidth={1.5} />
      </div>
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-desc">{description}</p>
    </div>
  );
}
