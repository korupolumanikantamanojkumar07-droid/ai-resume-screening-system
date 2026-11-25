import { useEffect, useState } from 'react';
import { Download, FileSpreadsheet, FileText } from 'lucide-react';
import { api } from '../api';
import { EmptyState, GlassCard, LoadingSpinner, PageHeader } from '../components/UI';

export default function ReportsPage() {
  const [jobs, setJobs] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [reports, setReports] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [selectedCandidateId, setSelectedCandidateId] = useState('');
  const [includePii, setIncludePii] = useState(false);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState('');
  const [msg, setMsg] = useState(null);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [jRes, rRes, repRes] = await Promise.all([
        api.listJobs(),
        api.listResumes({ limit: 200 }),
        api.listReports(),
      ]);
      const jList = jRes.items || [];
      const cList = (rRes.items || []).filter((r) => r.candidate_id);
      setJobs(jList);
      setCandidates(cList);
      setReports(repRes.items || []);
      if (jList.length > 0 && !selectedJobId) setSelectedJobId(String(jList[0].id));
      if (cList.length > 0 && !selectedCandidateId) setSelectedCandidateId(String(cList[0].candidate_id));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleGenerate = async (reportType) => {
    setGenerating(reportType);
    setMsg(null);
    try {
      const payload = {
        report_type: reportType,
        job_id: reportType !== 'candidate_pdf' ? Number(selectedJobId) : undefined,
        candidate_id: reportType === 'candidate_pdf' ? Number(selectedCandidateId) : undefined,
        include_pii: includePii,
      };
      const rep = await api.generateReport(payload);
      setMsg({ type: 'success', message: `Generated '${rep.title}'.` });
      await loadAll();
      window.open(api.reportDownloadUrl(rep.id), '_blank');
    } catch (e) {
      setMsg({ type: 'error', message: e.message });
    } finally {
      setGenerating('');
    }
  };

  if (loading) return <LoadingSpinner label="Loading screening reports..." />;

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Exports & Audit"
        title="Screening Reports"
        subtitle="Export ranked candidate tables to CSV, generate batch PDF screening reports, download individual candidate dossiers, and export skill gap analyses."
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard className="p-6 space-y-4">
          <h2 className="text-base font-semibold text-white">Job Screening Exports (CSV &amp; PDF)</h2>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Select Job Description</label>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900/80 border border-white/15 text-sm text-white"
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title}
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={includePii}
              onChange={(e) => setIncludePii(e.target.checked)}
              className="rounded border-white/20 bg-slate-900"
            />
            Include candidate names/emails in exported report (otherwise uses Anonymous IDs)
          </label>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-2">
            <button
              onClick={() => handleGenerate('rankings_csv')}
              disabled={!selectedJobId || generating !== ''}
              className="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white disabled:opacity-50"
            >
              <FileSpreadsheet className="w-4 h-4" />
              Rankings CSV
            </button>
            <button
              onClick={() => handleGenerate('batch_pdf')}
              disabled={!selectedJobId || generating !== ''}
              className="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl bg-violet-600 hover:bg-violet-500 text-xs font-semibold text-white disabled:opacity-50"
            >
              <FileText className="w-4 h-4" />
              Batch PDF
            </button>
            <button
              onClick={() => handleGenerate('skills_csv')}
              disabled={!selectedJobId || generating !== ''}
              className="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white disabled:opacity-50"
            >
              <FileSpreadsheet className="w-4 h-4" />
              Skills CSV
            </button>
          </div>
        </GlassCard>

        <GlassCard className="p-6 space-y-4">
          <h2 className="text-base font-semibold text-white">Individual Candidate PDF Report</h2>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Select Candidate</label>
            <select
              value={selectedCandidateId}
              onChange={(e) => setSelectedCandidateId(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900/80 border border-white/15 text-sm text-white"
            >
              {candidates.map((c) => (
                <option key={c.candidate_id} value={c.candidate_id}>
                  {c.candidate_name || c.anonymous_id} ({c.anonymous_id})
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={() => handleGenerate('candidate_pdf')}
            disabled={!selectedCandidateId || generating !== ''}
            className="inline-flex items-center gap-2 py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-violet-600 text-xs font-semibold text-white disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            Generate Individual Candidate PDF
          </button>
        </GlassCard>
      </div>

      {msg && (
        <div
          className={`p-3.5 rounded-xl border text-xs ${
            msg.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-400/30 text-emerald-200'
              : 'bg-rose-500/10 border-rose-400/30 text-rose-200'
          }`}
        >
          {msg.message}
        </div>
      )}

      <GlassCard className="p-6">
        <h2 className="text-base font-semibold text-white mb-4">Generated Reports History</h2>
        {reports.length === 0 ? (
          <EmptyState icon={FileText} title="No reports generated yet" description="Use the controls above to generate CSV or PDF reports." />
        ) : (
          <div className="space-y-2.5">
            {reports.map((rep) => (
              <div
                key={rep.id}
                className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-white/10"
              >
                <div>
                  <div className="text-sm font-medium text-white">{rep.title}</div>
                  <div className="text-xs text-slate-400 mt-0.5 uppercase">{rep.report_type.replace('_', ' ')}</div>
                </div>
                <a
                  href={api.reportDownloadUrl(rep.id)}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-xs font-medium text-white"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download
                </a>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  );
}
