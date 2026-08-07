import React from 'react';
import { Outlet } from 'react-router-dom';
import SideNav from './SideNav';
import './shell.css';

export default function AppShell() {
  return (
    <div className="app-shell">
      <SideNav />
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
