import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckSquare, Cpu, Play, Square, Sparkles } from 'lucide-react';
import { api } from '../api';
import { EmptyState, GlassCard, LoadingSpinner, PageHeader, ScoreBadge, SourceBadge, StatusBadge } from '../components/UI';

export default function ScreeningPage() {
  const [jobs, setJobs] = useState([]);
  const [resumes, setResumes] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [selectedResumeIds, setSelectedResumeIds] = useState([]);
  const [weights, setWeights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([api.listJobs(), api.listResumes({ limit: 250 }), api.getSettings()])
      .then(([jRes, rRes, sRes]) => {
        const jList = jRes.items || [];
        const rList = rRes.items || [];
        setJobs(jList);
        setResumes(rList);
        if (jList.length > 0) setSelectedJobId(String(jList[0].id));
        setSelectedResumeIds(rList.map((r) => r.id));
        setWeights(sRes.scoring_weights);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const toggleResume = (id) => {
    setSelectedResumeIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const selectBySource = (sourceType) => {
    if (sourceType === 'all') setSelectedResumeIds(resumes.map((r) => r.id));
    else if (sourceType === 'none') setSelectedResumeIds([]);
    else setSelectedResumeIds(resumes.filter((r) => r.source_type === sourceType).map((r) => r.id));
  };

  const handleRunScreening = async () => {
    if (!selectedJobId) {
      setError('Select a job description first.');
      return;
    }
    if (selectedResumeIds.length === 0) {
      setError('Select at least one resume to screen.');
      return;
    }
    setRunning(true);
    setError('');
    try {
      const res = await api.runScreening({
        job_id: Number(selectedJobId),
        resume_ids: selectedResumeIds,
        weights,
      });
      setResults(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setRunning(false);
    }
  };

  if (loading) return <LoadingSpinner label="Preparing AI Screening workspace..." />;

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Step 3 • Semantic Match & Ranking"
        title="AI Resume Screening"
        subtitle="Select a target job description and candidate resumes to compute semantic embeddings, TF-IDF alignment, and explainable rankings."
        actions={
          <button
            onClick={handleRunScreening}
            disabled={running || !selectedJobId || selectedResumeIds.length === 0}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 disabled:opacity-50 transition"
          >
            {running ? <Cpu className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {running ? 'Running NLP & Ranking...' : `Run AI Screening (${selectedResumeIds.length})`}
          </button>
        }
      />

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-400/30 text-rose-200 text-sm">{error}</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Job & Weight Configuration */}
        <GlassCard className="p-6 space-y-5">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              1. Target Job Description
            </label>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl bg-slate-900/90 border border-white/15 text-sm text-white focus:outline-none focus:border-blue-400"
            >
              {jobs.length === 0 && <option value="">No jobs available</option>}
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} ({j.required_skills?.length || 0} req skills)
                </option>
              ))}
            </select>
          </div>

          {weights && (
            <div className="space-y-2.5 pt-2 border-t border-white/10">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  2. Active Scoring Weights
                </span>
                <Link to="/settings" className="text-xs text-blue-400 hover:text-blue-300">
                  Customize
                </Link>
              </div>
              {Object.entries(weights).map(([k, v]) => (
                <div key={k} className="flex items-center justify-between text-xs text-slate-300">
                  <span className="capitalize">{k.replace('_', ' ')}</span>
                  <span className="font-mono text-blue-300">{v}%</span>
                </div>
              ))}
            </div>
          )}

          <div className="p-3.5 rounded-xl bg-blue-500/10 border border-blue-400/20 text-xs text-blue-200 leading-relaxed">
            Deterministic scoring: protected traits (age, gender, religion, caste, nationality, photos) are strictly excluded.
          </div>
        </GlassCard>

        {/* Resume Selector */}
        <GlassCard className="p-6 lg:col-span-2">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              3. Select Resumes ({selectedResumeIds.length} / {resumes.length} selected)
            </span>
            <div className="flex flex-wrap gap-1.5">
              <button
                onClick={() => selectBySource('all')}
                className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-xs text-slate-300"
              >
                All
              </button>
              <button
                onClick={() => selectBySource('uploaded')}
                className="px-2.5 py-1 rounded-lg bg-sky-500/15 hover:bg-sky-500/25 text-xs text-sky-300"
              >
                Uploaded Only
              </button>
              <button
                onClick={() => selectBySource('synthetic_demo')}
                className="px-2.5 py-1 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 text-xs text-amber-300"
              >
                Synthetic Demo
              </button>
              <button
                onClick={() => selectBySource('public_dataset')}
                className="px-2.5 py-1 rounded-lg bg-violet-500/15 hover:bg-violet-500/25 text-xs text-violet-300"
              >
                Dataset Only
              </button>
              <button
                onClick={() => selectBySource('none')}
                className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-xs text-slate-400"
              >
                Clear
              </button>
            </div>
          </div>

          {resumes.length === 0 ? (
            <EmptyState
              icon={Sparkles}
              title="No processed resumes"
              description="Upload resumes or load public datasets first."
            />
          ) : (
            <div className="max-h-72 overflow-y-auto space-y-2 pr-1">
              {resumes.map((r) => {
                const checked = selectedResumeIds.includes(r.id);
                return (
                  <div
                    key={r.id}
                    onClick={() => toggleResume(r.id)}
                    className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition ${
                      checked
                        ? 'bg-blue-600/15 border-blue-400/40'
                        : 'bg-slate-900/50 border-white/10 hover:border-white/20'
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      {checked ? (
                        <CheckSquare className="w-4 h-4 text-blue-400 shrink-0" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-500 shrink-0" />
                      )}
                      <div className="min-w-0">
                        <div className="text-sm font-medium text-white truncate">{r.candidate_name || r.filename}</div>
                        <div className="text-xs text-slate-400 truncate">
                          {r.experience_years} yrs • {r.education_level} • {r.skills_count} skills
                        </div>
                      </div>
                    </div>
                    <SourceBadge sourceType={r.source_type} />
                  </div>
                );
              })}
            </div>
          )}
        </GlassCard>
      </div>

      {/* Live Screening Output */}
      {results && (
        <GlassCard className="p-6">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
            <div>
              <h2 className="text-lg font-bold text-white">Screening Rankings: {results.job_title}</h2>
              <p className="text-xs text-slate-400">Screened {results.screened_count} candidate(s) successfully.</p>
            </div>
            <Link
              to={`/results?job_id=${results.job_id}`}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white"
            >
              Open Full Results &amp; Filters →
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-white/10 text-xs text-slate-400">
                  <th className="py-2.5 pr-3">Rank</th>
                  <th className="py-2.5 pr-3">Candidate</th>
                  <th className="py-2.5 pr-3">Overall</th>
                  <th className="py-2.5 pr-3">Req Skills</th>
                  <th className="py-2.5 pr-3">Semantic</th>
                  <th className="py-2.5 pr-3">Matched Skills</th>
                  <th className="py-2.5 pr-3">Missing Skills</th>
                  <th className="py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {results.results.map((r) => (
                  <tr key={r.id} className="hover:bg-white/5 transition">
                    <td className="py-3 pr-3 font-mono text-xs text-slate-300">#{r.rank_position}</td>
                    <td className="py-3 pr-3 font-medium text-white">
                      <Link to={`/candidates/${r.candidate_id}`} className="hover:text-blue-400">
                        {r.candidate_name}
                      </Link>
                    </td>
                    <td className="py-3 pr-3">
                      <ScoreBadge score={r.overall_score} />
                    </td>
                    <td className="py-3 pr-3 font-mono text-xs text-slate-300">{r.required_skill_score.toFixed(0)}%</td>
                    <td className="py-3 pr-3 font-mono text-xs text-violet-300">
                      {r.semantic_similarity_score.toFixed(0)}%
                    </td>
                    <td className="py-3 pr-3">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {(r.matched_skills || []).slice(0, 4).map((s) => (
                          <span key={s} className="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 text-[11px]">
                            {s}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3 pr-3">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {(r.missing_skills || []).slice(0, 4).map((s) => (
                          <span key={s} className="px-1.5 py-0.5 rounded bg-rose-500/15 text-rose-300 text-[11px]">
                            {s}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3">
                      <StatusBadge status={r.screening_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      )}
    </div>
  );
}
