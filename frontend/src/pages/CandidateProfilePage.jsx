import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Award,
  Briefcase,
  CheckCircle2,
  Download,
  GraduationCap,
  Mail,
  MapPin,
  Phone,
  Sparkles,
  XCircle,
} from 'lucide-react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api';
import { EmptyState, GlassCard, LoadingSpinner, PageHeader, ScoreBadge, SourceBadge, StatusBadge } from '../components/UI';

export default function CandidateProfilePage() {
  const { id } = useParams();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api
      .getCandidateProfile(id)
      .then(setProfile)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleDownloadPdf = async () => {
    setDownloading(true);
    try {
      const rep = await api.generateReport({
        candidate_id: Number(id),
        report_type: 'candidate_pdf',
      });
      window.open(api.reportDownloadUrl(rep.id), '_blank');
    } catch (e) {
      alert(e.message);
    } finally {
      setDownloading(false);
    }
  };

  if (loading) return <LoadingSpinner label="Loading candidate NLP profile..." />;
  if (error || !profile) return <EmptyState icon={Sparkles} title="Candidate not found" description={error} />;

  const activeEval = profile.evaluations?.[0];
  const breakdownData = activeEval
    ? [
        { metric: 'Req Skills', score: activeEval.required_skill_score },
        { metric: 'Semantic', score: activeEval.semantic_similarity_score },
        { metric: 'TF-IDF', score: activeEval.tfidf_similarity_score },
        { metric: 'Experience', score: activeEval.experience_score },
        { metric: 'Education', score: activeEval.education_score },
        { metric: 'Preferred', score: activeEval.preferred_skill_score },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link to="/results" className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-white">
          <ArrowLeft className="w-4 h-4" />
          Back to Candidate Results
        </Link>
        <button
          onClick={handleDownloadPdf}
          disabled={downloading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-violet-600 text-xs font-semibold text-white shadow-lg shadow-blue-600/20"
        >
          <Download className="w-3.5 h-3.5" />
          {downloading ? 'Generating PDF...' : 'Download Candidate PDF Report'}
        </button>
      </div>

      <PageHeader
        badge={`Candidate ID: ${profile.anonymous_id}`}
        title={profile.display_name}
        subtitle={`Extracted from ${profile.filename} (${profile.ocr_used ? 'OCR Processed' : 'Direct Text Extraction'})`}
        actions={<SourceBadge sourceType={profile.source_type} />}
      />

      {/* Contact & Key Facts */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <GlassCard className="p-4 flex items-center gap-3">
          <Mail className="w-4 h-4 text-blue-400 shrink-0" />
          <div className="min-w-0">
            <div className="text-[11px] text-slate-400">Email</div>
            <div className="text-xs font-medium text-white truncate">{profile.email || 'Not detected'}</div>
          </div>
        </GlassCard>
        <GlassCard className="p-4 flex items-center gap-3">
          <Phone className="w-4 h-4 text-violet-400 shrink-0" />
          <div className="min-w-0">
            <div className="text-[11px] text-slate-400">Phone</div>
            <div className="text-xs font-medium text-white truncate">{profile.phone || 'Not detected'}</div>
          </div>
        </GlassCard>
        <GlassCard className="p-4 flex items-center gap-3">
          <Briefcase className="w-4 h-4 text-emerald-400 shrink-0" />
          <div>
            <div className="text-[11px] text-slate-400">Experience</div>
            <div className="text-xs font-medium text-white">{profile.total_experience_years} Years</div>
          </div>
        </GlassCard>
        <GlassCard className="p-4 flex items-center gap-3">
          <GraduationCap className="w-4 h-4 text-sky-400 shrink-0" />
          <div className="min-w-0">
            <div className="text-[11px] text-slate-400">Education</div>
            <div className="text-xs font-medium text-white truncate">
              {profile.education_level} {profile.graduation_year ? `(${profile.graduation_year})` : ''}
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Detailed Scoring Breakdown */}
      {activeEval && (
        <GlassCard className="p-6">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
            <div>
              <h2 className="text-base font-semibold text-white">
                Scoring Breakdown — {activeEval.job_title} (Rank #{activeEval.rank_position})
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                {activeEval.explanation?.decision_support_notice}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <ScoreBadge score={activeEval.overall_score} />
              <StatusBadge status={activeEval.screening_status} />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-center">
            <div className="h-60">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={breakdownData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
                  <XAxis dataKey="metric" stroke="#94a3b8" fontSize={11} />
                  <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      border: '1px solid rgba(148,163,184,0.2)',
                      borderRadius: '12px',
                    }}
                  />
                  <Bar dataKey="score" fill="#3B82F6" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-300 mb-2 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Matched Requirements
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {(activeEval.matched_skills || []).length > 0 ? (
                    activeEval.matched_skills.map((s) => (
                      <span key={s} className="px-2.5 py-1 rounded-lg bg-emerald-500/15 border border-emerald-400/25 text-emerald-200 text-xs">
                        {s}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-400">None</span>
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-rose-300 mb-2 flex items-center gap-1.5">
                  <XCircle className="w-3.5 h-3.5" /> Missing Requirements
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {(activeEval.missing_skills || []).length > 0 ? (
                    activeEval.missing_skills.map((s) => (
                      <span key={s} className="px-2.5 py-1 rounded-lg bg-rose-500/15 border border-rose-400/25 text-rose-200 text-xs">
                        {s}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-emerald-300">All required skills matched!</span>
                  )}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/70 border border-white/10 text-xs text-slate-300 space-y-1">
                <div>• {activeEval.explanation?.experience_note}</div>
                <div>• {activeEval.explanation?.education_note}</div>
                <div>
                  • Raw Cosine Similarity: <span className="font-mono text-blue-300">{activeEval.explanation?.raw_cosine_similarity}</span>{' '}
                  | TF-IDF Cosine: <span className="font-mono text-violet-300">{activeEval.explanation?.tfidf_cosine_similarity}</span>
                </div>
              </div>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Extracted Technical & Soft Skills */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard className="p-6">
          <h2 className="text-base font-semibold text-white mb-4">Extracted Skills &amp; Match Method</h2>
          <div className="flex flex-wrap gap-2">
            {(profile.skills || []).map((sk) => (
              <div
                key={sk.id}
                className="px-3 py-1.5 rounded-xl bg-slate-900/80 border border-white/10 text-xs flex items-center gap-2"
              >
                <span className="font-medium text-white">{sk.name}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/15 text-blue-300 capitalize">
                  {sk.match_method}
                </span>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard className="p-6 space-y-4">
          <h2 className="text-base font-semibold text-white">Education, Projects &amp; Certifications</h2>
          <div className="text-xs text-slate-300 space-y-2">
            <div>
              <span className="text-slate-400 font-semibold">Degree / University:</span>{' '}
              {profile.degree || 'Not parsed'} {profile.university ? `— ${profile.university}` : ''}
            </div>
            {profile.location && (
              <div className="flex items-center gap-1.5 text-slate-300">
                <MapPin className="w-3.5 h-3.5 text-slate-400" /> {profile.location}
              </div>
            )}
            {profile.certifications?.length > 0 && (
              <div>
                <div className="text-slate-400 font-semibold mb-1 flex items-center gap-1">
                  <Award className="w-3.5 h-3.5 text-amber-400" /> Certifications
                </div>
                <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                  {profile.certifications.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </div>
            )}
            {profile.projects?.length > 0 && (
              <div>
                <div className="text-slate-400 font-semibold mb-1">Projects</div>
                <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                  {profile.projects.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </GlassCard>
      </div>

      {/* Work Experience */}
      <GlassCard className="p-6">
        <h2 className="text-base font-semibold text-white mb-3">Extracted Work Experience &amp; Summary</h2>
        <p className="text-xs text-slate-300 leading-relaxed mb-3">{profile.experience_summary}</p>
        {profile.work_experience?.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {profile.work_experience.map((w, i) => (
              <div key={i} className="p-3 rounded-xl bg-slate-900/60 border border-white/10 text-xs text-slate-200">
                {w}
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  );
}
