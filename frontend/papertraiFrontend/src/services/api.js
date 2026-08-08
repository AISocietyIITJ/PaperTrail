const API_BASE = 'http://localhost:8000';

export async function getResearchPath(query, maxHops = 3) {
  const response = await fetch(`${API_BASE}/usecase1/get-reading-path`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query_str: query, config_path: "config.yaml" })
  });
  if (!response.ok) throw new Error('Failed to fetch research path');
  return response.json();
}

export async function getFacultyMatches(resumeFile, interests) {
  // If we have a file, we could send it as FormData, but the backend accepts resume_text or query.
  // For simplicity based on the mocked flow, we'll send the interests array as a joined query string.
  const queryStr = interests ? (Array.isArray(interests) ? interests.join(", ") : interests) : "research interests";
  const response = await fetch(`${API_BASE}/usecase2/find-academic-profiles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: queryStr, resume_path: null, resume_text: null })
  });
  if (!response.ok) throw new Error('Failed to fetch faculty matches');
  const data = await response.json();

  const professors = data.professors || [];
  const mappedMatches = professors.map(prof => ({
    facultyId: prof.profile_url || prof.professor_name,
    name: prof.professor_name
      ? prof.professor_name.split(' ').map(n => n.charAt(0).toUpperCase() + n.slice(1)).join(' ')
      : "Unknown Professor",
    department: prof.affiliation
      ? prof.affiliation.split(' ').map(n => n.charAt(0).toUpperCase() + n.slice(1)).join(' ')
      : "Affiliation Unknown",
    matchScore: prof.matching_interest_count ? Math.min(prof.matching_interest_count * 0.15 + 0.5, 0.99) : 0.5,
    summary: `Strongly matches your profile based on shared interests: ${prof.matched_interests ? prof.matched_interests.join(', ') : 'N/A'}. They have an h-index of ${prof.h_index} and ${prof.cited_by} total citations.`,
    evidencePapers: [], // Backend does not return individual evidence papers yet
    profileUrl: prof.profile_url
  }));

  return { matches: mappedMatches };
}

export async function getProblemCloud(query) {
  const response = await fetch(`${API_BASE}/usecase3/recommend_papers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: query, top_n: 10 })
  });
  if (!response.ok) throw new Error('Failed to fetch problem cloud');
  const data = await response.json();
  // Backend returns a list of papers: [{score, title, published_date, abstract}, ...]
  // We need to map this to what the ProblemCloudCanvas expects:
  // { query: ..., papers: [{nodeIdx, title, abstract, relevance, ...}, ...] }
  return {
    query: query,
    papers: data.map((p, idx) => ({
      nodeIdx: idx,
      title: p.title,
      abstract: p.abstract,
      publishedDate: p.published_date,
      relevance: p.score,
      arxivId: p.arxiv_id,
      arxivUrl: p.arxiv_id ? `https://arxiv.org/abs/${p.arxiv_id}` : '',
      pdfUrl: p.arxiv_id ? `https://arxiv.org/pdf/${p.arxiv_id}.pdf` : '',
      authors: []
    }))
  };
}
