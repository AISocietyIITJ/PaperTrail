import React from 'react';
import { NavLink } from 'react-router-dom';
import { Map, Users, Lightbulb } from 'lucide-react';
import './shell.css';

export default function SideNav() {
  return (
    <nav className="side-nav">
      <div className="brand">
        <h1>PaperTrail</h1>
      </div>
      <ul className="nav-links">
        <li>
          <NavLink to="/" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>
            <Map size={20} />
            <span>Research Path</span>
          </NavLink>
        </li>
        <li>
          <NavLink to="/researcher-match" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>
            <Users size={20} />
            <span>Researcher Match</span>
          </NavLink>
        </li>
        <li>
          <NavLink to="/problem-discovery" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>
            <Lightbulb size={20} />
            <span>Problem Discovery</span>
          </NavLink>
        </li>
      </ul>
    </nav>
  );
}
