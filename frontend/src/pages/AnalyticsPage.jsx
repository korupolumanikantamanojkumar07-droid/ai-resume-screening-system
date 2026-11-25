import { useEffect, useState } from 'react';
import { BarChart3 } from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api } from '../api';
import { EmptyState, GlassCard, LoadingSpinner, PageHeader } from '../components/UI';

const COLORS = ['#3B82F6', '#8B5CF6', '#0EA5E9', '#10B981', '#F59E0B', '#EC4899'];

export default function AnalyticsPage() {
  const [jobs, setJobs] = useState([]);
  const [jobId, setJobId] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadAnalytics = async (selectedJob) => {
    setLoading(true);
    try {
      const [jRes, aRes] = await Promise.all([api.listJobs(), api.getAnalytics(selectedJob || undefined)]);
      setJobs(jRes.items || []);
      setData(aRes);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics(jobId);
  }, [jobId]);

  if (loading) return <LoadingSpinner label="Preparing hiring analytics..." />;
  if (!data) return <EmptyState icon={BarChart3} title="No analytics available yet" />;

  const rs = data.ranking_stats;

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Hiring Insights"
        title="Talent & Skill Analytics"
        subtitle="Visual breakdown of role compatibility scores, skill gaps, experience levels, and education across applicants."
        actions={
          <select
            value={jobId}
            onChange={(e) => setJobId(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-900/90 border border-white/15 text-xs text-white"
          >
            <option value="">All Open Roles</option>
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.title}
              </option>
            ))}
          </select>
        }
      />

      {/* Summary Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Evaluated', val: rs.total_screened },
          { label: 'Mean Fit', val: `${rs.mean_score}%` },
          { label: 'Median Fit', val: `${rs.median_score}%` },
          { label: 'Highest Fit', val: `${rs.max_score}%` },
          { label: 'Top 10% Cutoff', val: `${rs.p90_score}%` },
          { label: 'Shortlisted', val: rs.shortlisted_count },
        ].map((item) => (
          <GlassCard key={item.label} className="p-4 text-center">
            <div className="text-[11px] text-slate-400">{item.label}</div>
            <div className="text-xl font-display font-bold text-white mt-1">{item.val}</div>
          </GlassCard>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard className="p-6">
          <h2 className="text-base font-semibold text-white mb-4">Candidate Fit Score Distribution</h2>
          <div className="h-68">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.score_distribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
                <XAxis dataKey="range" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderRadius: '12px', border: '1px solid rgba(148,163,184,0.2)' }} />
                <Bar dataKey="count" name="Candidates" fill="#3B82F6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard className="p-6">
          <h2 className="text-base font-semibold text-white mb-4">Skill Gaps vs. Matched Skills</h2>
          <div className="h-68">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.missing_skills_analysis} margin={{ bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
                <XAxis dataKey="skill" stroke="#94a3b8" fontSize={11} angle={20} textAnchor="end" interval={0} />
                <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderRadius: '12px', border: '1px solid rgba(148,163,184,0.2)' }} />
                <Legend />
                <Bar dataKey="missing_count" name="Missing" fill="#F43F5E" radius={[4, 4, 0, 0]} />
                <Bar dataKey="matched_count" name="Matched" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard className="p-6">
          <h2 className="text-base font-semibold text-white mb-4">Most Common Skills Among Applicants</h2>
          <div className="h-68">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.most_common_skills} margin={{ bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
                <XAxis dataKey="skill" stroke="#94a3b8" fontSize={11} angle={25} textAnchor="end" interval={0} />
                <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderRadius: '12px', border: '1px solid rgba(148,163,184,0.2)' }} />
                <Bar dataKey="count" name="Applicants" fill="#8B5CF6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard className="p-6">
          <h2 className="text-base font-semibold text-white mb-4">Experience &amp; Education Breakdown</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 h-68">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.experience_distribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
                <XAxis dataKey="bucket" stroke="#94a3b8" fontSize={10} />
                <YAxis stroke="#94a3b8" fontSize={10} allowDecimals={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderRadius: '12px' }} />
                <Bar dataKey="count" name="Applicants" fill="#0EA5E9" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>

            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={data.education_distribution} dataKey="count" nameKey="level" cx="50%" cy="50%" outerRadius={72}>
                  {data.education_distribution.map((_, idx) => (
                    <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderRadius: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
