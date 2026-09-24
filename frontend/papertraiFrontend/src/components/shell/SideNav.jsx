import React, { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Map, Users, Lightbulb, Menu, X } from 'lucide-react';
import './shell.css';

export default function SideNav() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  // Close sidebar on route change (mobile)
  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  // Prevent body scroll when mobile nav is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  const navLinks = [
    { to: '/', label: 'Research Path', icon: Map, end: true },
    { to: '/researcher-match', label: 'Researcher Match', icon: Users },
    { to: '/problem-discovery', label: 'Problem Discovery', icon: Lightbulb },
  ];

  return (
    <>
      {/* Mobile top bar */}
      <header className="mobile-header">
        <button
          className="burger-btn"
          onClick={() => setIsOpen(true)}
          aria-label="Open navigation menu"
          aria-expanded={isOpen}
        >
          <Menu size={24} />
        </button>
        <span className="mobile-brand">PaperTrail</span>
      </header>

      {/* Overlay (mobile only) */}
      {isOpen && (
        <div
          className="nav-overlay"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <nav className={`side-nav ${isOpen ? 'side-nav--open' : ''}`} aria-label="Main navigation">
        <div className="brand">
          <h1>PaperTrail</h1>
          <button
            className="nav-close-btn"
            onClick={() => setIsOpen(false)}
            aria-label="Close navigation menu"
          >
            <X size={20} />
          </button>
        </div>
        <ul className="nav-links">
          {navLinks.map(({ to, label, icon: Icon, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
              >
                <Icon size={20} />
                <span>{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </>
  );
}
