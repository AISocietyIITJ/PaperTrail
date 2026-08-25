import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppShell from './components/shell/AppShell';
import ResearchPath from './routes/ResearchPath';
import ResearcherMatch from './routes/ResearcherMatch';
import ProblemDiscovery from './routes/ProblemDiscovery';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<ResearchPath />} />
          <Route path="researcher-match" element={<ResearcherMatch />} />
          <Route path="problem-discovery" element={<ProblemDiscovery />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
