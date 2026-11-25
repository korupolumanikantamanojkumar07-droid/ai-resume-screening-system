import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowUpDown, Filter, Users } from 'lucide-react';
import { api } from '../api';
import { EmptyState, GlassCard, LoadingSpinner, PageHeader, ScoreBadge, SourceBadge } from '../components/UI';

export default function ResultsPage() {
  const [searchParams] = useSearchParams();
  const [jobs, setJobs] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  const [filters, setFilters] = useState({
    job_id: searchParams.get('job_id') || '',
    min_score: 0,
    skill: '',
    min_experience: 0,
    education_level: 'all',
    source_type: 'all',
    sort_by: 'overall_score',
    sort_dir: 'desc',
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [jRes, rRes] = await Promise.all([api.listJobs(), api.listScreeningResults(filters)]);
      setJobs(jRes.items || []);
      setResults(rRes.items || []);
    } catch {
      // handled gracefully
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filters.job_id, filters.education_level, filters.source_type, filters.sort_by, filters.sort_dir]);

  const toggleSort = (field) => {
    setFilters((prev) => ({
      ...prev,
      sort_by: field,
      sort_dir: prev.sort_by === field && prev.sort_dir === 'desc' ? 'asc' : 'desc',
    }));
  };

  const handleStatusChange = async (resultId, newStatus) => {
    try {
      await api.updateScreeningStatus(resultId, newStatus);
      setResults((prev) => prev.map((r) => (r.id === resultId ? { ...r, screening_status: newStatus } : r)));
    } catch {
      // ignore
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Explainable Rankings"
        title="Candidate Results"
        subtitle="Filter, sort, and review evaluated candidates across job requisitions. Click any candidate for full NLP extraction & scoring breakdown."
      />

      {/* Filter Bar */}
      <GlassCard className="p-5">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
          <Filter className="w-3.5 h-3.5 text-blue-400" />
          Filter Candidates
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          <select
            value={filters.job_id}
            onChange={(e) => setFilters({ ...filters, job_id: e.target.value })}
            className="px-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-white"
          >
            <option value="">All Job Roles</option>
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.title}
              </option>
            ))}
          </select>

          <input
            type="text"
            value={filters.skill}
            onChange={(e) => setFilters({ ...filters, skill: e.target.value })}
            placeholder="Filter by skill (e.g. Python)"
            className="px-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-white placeholder-slate-500"
          />

          <div>
            <input
              type="number"
              min={0}
              max={100}
              value={filters.min_score}
              onChange={(e) => setFilters({ ...filters, min_score: Number(e.target.value) || 0 })}
              placeholder="Min Score %"
              className="w-full px-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-white"
            />
          </div>

          <div>
            <input
              type="number"
              min={0}
              max={40}
              value={filters.min_experience}
              onChange={(e) => setFilters({ ...filters, min_experience: Number(e.target.value) || 0 })}
              placeholder="Min Exp (yrs)"
              className="w-full px-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-white"
            />
          </div>

          <select
            value={filters.education_level}
            onChange={(e) => setFilters({ ...filters, education_level: e.target.value })}
            className="px-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-white"
          >
            <option value="all">Any Education</option>
            <option value="Bachelor's">Bachelor's</option>
            <option value="Master's">Master's</option>
            <option value="PhD">PhD</option>
            <option value="Diploma">Diploma</option>
          </select>

          <div className="flex gap-2">
            <select
              value={filters.source_type}
              onChange={(e) => setFilters({ ...filters, source_type: e.target.value })}
              className="flex-1 px-2.5 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-white"
            >
              <option value="all">All Sources</option>
              <option value="uploaded">Uploaded</option>
              <option value="synthetic_demo">Synthetic Demo</option>
              <option value="public_dataset">Dataset</option>
            </select>
            <button
              onClick={loadData}
              className="px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white"
            >
              Apply
            </button>
          </div>
        </div>
      </GlassCard>

      {/* Results Table */}
      <GlassCard className="p-6">
        {loading ? (
          <LoadingSpinner label="Loading screening results..." />
        ) : results.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No candidate screening results match your filters"
            description="Run AI Screening on a job description or relax the active filter criteria."
            action={
              <Link to="/screening" className="px-4 py-2 rounded-xl bg-blue-600 text-xs font-semibold text-white">
                Go to AI Screening
              </Link>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-white/10 text-xs text-slate-400">
                  <th className="py-3 pr-3 cursor-pointer hover:text-white" onClick={() => toggleSort('rank_position')}>
                    <span className="inline-flex items-center gap-1">
                      Rank <ArrowUpDown className="w-3 h-3" />
                    </span>
                  </th>
                  <th className="py-3 pr-3">Candidate</th>
                  <th className="py-3 pr-3">Job Role</th>
                  <th className="py-3 pr-3 cursor-pointer hover:text-white" onClick={() => toggleSort('overall_score')}>
                    <span className="inline-flex items-center gap-1">
                      Match % <ArrowUpDown className="w-3 h-3" />
                    </span>
                  </th>
                  <th className="py-3 pr-3">Skills Matched</th>
                  <th className="py-3 pr-3 cursor-pointer hover:text-white" onClick={() => toggleSort('experience_years')}>
                    <span className="inline-flex items-center gap-1">
                      Experience <ArrowUpDown className="w-3 h-3" />
                    </span>
                  </th>
                  <th className="py-3 pr-3">Education</th>
                  <th className="py-3">Screening Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {results.map((r) => (
                  <tr key={r.id} className="hover:bg-white/5 transition">
                    <td className="py-3.5 pr-3 font-mono text-xs text-slate-300">#{r.rank_position}</td>
                    <td className="py-3.5 pr-3">
                      <Link to={`/candidates/${r.candidate_id}`} className="font-medium text-white hover:text-blue-400">
                        {r.candidate_name}
                      </Link>
                      <div className="mt-1">
                        <SourceBadge sourceType={r.source_type} />
                      </div>
                    </td>
                    <td className="py-3.5 pr-3 text-xs text-slate-300">{r.job_title}</td>
                    <td className="py-3.5 pr-3">
                      <ScoreBadge score={r.overall_score} />
                      <div className="text-[10px] text-slate-400 mt-1">Sem: {r.semantic_similarity_score.toFixed(0)}%</div>
                    </td>
                    <td className="py-3.5 pr-3">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {(r.matched_skills || []).slice(0, 4).map((s) => (
                          <span key={s} className="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 text-[11px]">
                            {s}
                          </span>
                        ))}
                        {(r.missing_skills || []).slice(0, 2).map((s) => (
                          <span key={s} className="px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-300/80 text-[11px] line-through">
                            {s}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3.5 pr-3 font-mono text-xs text-slate-300">{r.experience_years} yrs</td>
                    <td className="py-3.5 pr-3 text-xs text-slate-300">{r.education_level}</td>
                    <td className="py-3.5">
                      <select
                        value={r.screening_status}
                        onChange={(e) => handleStatusChange(r.id, e.target.value)}
                        className="px-2.5 py-1 rounded-lg bg-slate-900 border border-white/15 text-xs text-slate-200 focus:outline-none focus:border-blue-400"
                      >
                        <option value="screened">Screened</option>
                        <option value="shortlisted">Shortlisted</option>
                        <option value="review">In Review</option>
                        <option value="rejected">Rejected</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>
    </div>
  );
}
