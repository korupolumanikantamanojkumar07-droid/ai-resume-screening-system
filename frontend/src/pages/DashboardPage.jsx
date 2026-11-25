import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  Award,
  Briefcase,
  FileText,
  Sparkles,
  UploadCloud,
  Users,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api } from '../api';
import { EmptyState, GlassCard, LoadingSpinner, PageHeader, ScoreBadge, StatusBadge } from '../components/UI';

const CHART_COLORS = ['#3B82F6', '#8B5CF6', '#0EA5E9', '#10B981', '#F59E0B', '#EC4899'];

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .getDashboard()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner label="Loading HR pipeline overview..." />;
  if (error) return <EmptyState icon={Activity} title="Unable to load dashboard" description={error} />;

  const s = data.stats;
  const kpis = [
    {
      label: 'Candidates in Pipeline',
      value: s.total_candidates,
      sub: `${s.uploaded_resumes} newly uploaded CVs`,
      icon: Users,
      color: 'text-blue-400',
    },
    {
      label: 'Active Job Openings',
      value: s.active_jobs,
      sub: 'Ready for candidate screening',
      icon: Briefcase,
      color: 'text-violet-400',
    },
    {
      label: 'Evaluations Completed',
      value: s.total_screenings,
      sub: 'Role-candidate fit assessments',
      icon: FileText,
      color: 'text-sky-400',
    },
    {
      label: 'Average Role Fit',
      value: `${s.average_matching_score}%`,
      sub: 'Across screened applicants',
      icon: Award,
      color: 'text-emerald-400',
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        badge="HR Overview"
        title="Hiring Pipeline Dashboard"
        subtitle="Track applicant intake, active job requisitions, top-ranked candidates, and skill availability across your company."
        actions={
          <>
            <Link
              to="/upload"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/15 text-sm font-medium text-white transition"
            >
              <UploadCloud className="w-4 h-4 text-blue-400" />
              Upload Resumes
            </Link>
            <Link
              to="/screening"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition"
            >
              <Sparkles className="w-4 h-4" />
              Screen Candidates
            </Link>
          </>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {kpis.map((k) => {
          const Icon = k.icon;
          return (
            <GlassCard key={k.label} hover className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-xs font-medium text-slate-400">{k.label}</div>
                  <div className="text-3xl font-display font-bold text-white mt-1">{k.value}</div>
                  <div className="text-xs text-slate-400 mt-1.5">{k.sub}</div>
                </div>
                <div className={`p-2.5 rounded-xl bg-white/5 border border-white/10 ${k.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
              </div>
            </GlassCard>
          );
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <GlassCard className="p-6 lg:col-span-2">
          <h2 className="text-base font-semibold text-white mb-4">Top Skills Across Candidate Pool</h2>
          {data.skills_distribution.length === 0 ? (
            <EmptyState
              icon={Users}
              title="No candidate skills yet"
              description="Upload applicant CVs to view skill coverage across your pipeline."
            />
          ) : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.skills_distribution} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} angle={25} textAnchor="end" interval={0} />
                  <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      border: '1px solid rgba(148,163,184,0.2)',
                      borderRadius: '12px',
                      color: '#f8fafc',
                    }}
                  />
                  <Bar dataKey="count" name="Candidates" radius={[6, 6, 0, 0]}>
                    {data.skills_distribution.map((_, idx) => (
                      <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </GlassCard>

        <GlassCard className="p-6">
          <h2 className="text-base font-semibold text-white mb-4">Talent Pool Breakdown</h2>
          {data.category_distribution.length === 0 ? (
            <EmptyState icon={FileText} title="No applicants yet" description="Upload resumes to begin." />
          ) : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.category_distribution}
                    dataKey="count"
                    nameKey="category"
                    cx="50%"
                    cy="48%"
                    innerRadius={52}
                    outerRadius={86}
                    paddingAngle={3}
                  >
                    {data.category_distribution.map((_, idx) => (
                      <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      border: '1px solid rgba(148,163,184,0.2)',
                      borderRadius: '12px',
                      color: '#f8fafc',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </GlassCard>
      </div>

      {/* Ranking Overview & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <GlassCard className="p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-white">Top Ranked Candidates</h2>
            <Link to="/results" className="text-xs font-medium text-blue-400 hover:text-blue-300">
              View Full Shortlist →
            </Link>
          </div>
          {data.ranking_overview.length === 0 ? (
            <EmptyState
              icon={Award}
              title="No candidate rankings yet"
              description="Evaluate applicants against an open role to generate ranked shortlists."
              action={
                <Link
                  to="/screening"
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white"
                >
                  Run Screening
                </Link>
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-xs text-slate-400">
                    <th className="py-2.5 pr-3">Rank</th>
                    <th className="py-2.5 pr-3">Candidate</th>
                    <th className="py-2.5 pr-3">Target Role</th>
                    <th className="py-2.5 pr-3">Role Fit</th>
                    <th className="py-2.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {data.ranking_overview.map((row) => (
                    <tr key={row.id} className="hover:bg-white/5 transition">
                      <td className="py-3 pr-3 font-mono text-xs text-slate-300">#{row.rank_position}</td>
                      <td className="py-3 pr-3 font-medium text-white">
                        <Link to={`/candidates/${row.candidate_id}`} className="hover:text-blue-400 transition">
                          {row.candidate_name}
                        </Link>
                      </td>
                      <td className="py-3 pr-3 text-slate-300 text-xs">{row.job_title}</td>
                      <td className="py-3 pr-3">
                        <ScoreBadge score={row.overall_score} />
                      </td>
                      <td className="py-3">
                        <StatusBadge status={row.screening_status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </GlassCard>

        <GlassCard className="p-6">
          <h2 className="text-base font-semibold text-white mb-4">Recent Hiring Activity</h2>
          {data.recent_activity.length === 0 ? (
            <p className="text-sm text-slate-400">No recent activity yet.</p>
          ) : (
            <div className="space-y-3">
              {data.recent_activity.slice(0, 6).map((act, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-slate-900/60 border border-white/10">
                  <div className="text-xs font-medium text-slate-200">{act.title}</div>
                  <div className="flex items-center justify-between mt-1.5 text-[11px] text-slate-400">
                    <span className="capitalize">{act.type === 'screening' ? 'Evaluation' : 'Intake'}</span>
                    {act.score !== null && <ScoreBadge score={act.score} />}
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
}
