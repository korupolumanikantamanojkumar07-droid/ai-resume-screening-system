const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const err = await res.json();
      msg = err.detail || err.message || msg;
    } catch {
      // ignore json parse failure
    }
    throw new Error(msg);
  }
  return res.json();
}

export const api = {
  getBaseUrl: () => API_BASE,

  health: () => request('/health'),

  // Dashboard
  getDashboard: () => request('/dashboard/overview'),

  // Resumes
  listResumes: (params = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') qs.set(k, String(v));
    });
    return request(`/resumes?${qs.toString()}`);
  },
  uploadResumes: (files) => {
    const fd = new FormData();
    files.forEach((f) => fd.append('files', f));
    return request('/resumes/upload', { method: 'POST', body: fd });
  },
  replaceResume: (resumeId, file) => {
    const fd = new FormData();
    fd.append('file', file);
    return request(`/resumes/${resumeId}/replace`, { method: 'PUT', body: fd });
  },
  deleteResume: (resumeId) => request(`/resumes/${resumeId}`, { method: 'DELETE' }),

  // Jobs
  listJobs: () => request('/jobs'),
  analyzeJob: (payload) =>
    request('/jobs/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  createJob: (payload) =>
    request('/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  updateJob: (id, payload) =>
    request(`/jobs/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  deleteJob: (id) => request(`/jobs/${id}`, { method: 'DELETE' }),

  // Screening & Candidates
  runScreening: (payload) =>
    request('/screening/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  listScreeningResults: (params = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '' && v !== 'all') qs.set(k, String(v));
    });
    return request(`/screening/results?${qs.toString()}`);
  },
  updateScreeningStatus: (resultId, screening_status) =>
    request(`/screening/results/${resultId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ screening_status }),
    }),
  getCandidateProfile: (candidateId) => request(`/candidates/${candidateId}`),

  // Analytics
  getAnalytics: (jobId) => request(`/analytics/overview${jobId ? `?job_id=${jobId}` : ''}`),

  // Reports
  listReports: () => request('/reports'),
  generateReport: (payload) =>
    request('/reports/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  reportDownloadUrl: (reportId) => `${API_BASE}/reports/${reportId}/download`,

  // Settings & Datasets
  getSettings: () => request('/settings'),
  updateWeights: (weights) =>
    request('/settings/weights', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(weights),
    }),
  updatePrivacy: (privacy) =>
    request('/settings/privacy', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(privacy),
    }),
  purgeExpired: () => request('/settings/purge-expired', { method: 'POST' }),
  addSkill: (skill) =>
    request('/settings/skills', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(skill),
    }),
  deleteSkill: (skillId) => request(`/settings/skills/${skillId}`, { method: 'DELETE' }),
  loadDatasets: (payload) =>
    request('/settings/datasets/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  loadInitialDemo: () => request('/settings/datasets/load-initial', { method: 'POST' }),
};
