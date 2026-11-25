import { useEffect, useState } from 'react';
import { Briefcase, Plus, Trash2, Wand2 } from 'lucide-react';
import { api } from '../api';
import { EmptyState, GlassCard, LoadingSpinner, PageHeader } from '../components/UI';

const EMPTY_FORM = {
  title: '',
  department: 'Engineering',
  description: '',
  required_skills_text: '',
  preferred_skills_text: '',
  min_experience_years: 2,
  education_requirement: "Bachelor's",
  additional_qualifications: '',
};

export default function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(EMPTY_FORM);
  const [analyzing, setAnalyzing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const res = await api.listJobs();
      setJobs(res.items || []);
    } catch (e) {
      setMsg({ type: 'error', message: e.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  const handleAutoExtract = async () => {
    if (!form.description || form.description.trim().length < 15) {
      setMsg({ type: 'error', message: 'Please paste a job description (at least 15 characters) first.' });
      return;
    }
    setAnalyzing(true);
    setMsg(null);
    try {
      const res = await api.analyzeJob({ title: form.title, description: form.description });
      setForm((prev) => ({
        ...prev,
        required_skills_text: (res.required_skills || []).join(', '),
        preferred_skills_text: (res.preferred_skills || []).join(', '),
        min_experience_years: res.min_experience_years ?? prev.min_experience_years,
        education_requirement:
          res.education_requirement && res.education_requirement !== 'Unspecified'
            ? res.education_requirement
            : prev.education_requirement,
        additional_qualifications: res.additional_qualifications || prev.additional_qualifications,
      }));
      setMsg({
        type: 'success',
        message: `Extracted ${res.required_skills?.length || 0} required skills and ${res.preferred_skills?.length || 0} preferred skills.`,
      });
    } catch (e) {
      setMsg({ type: 'error', message: e.message });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!form.title.trim() || form.description.trim().length < 20) {
      setMsg({ type: 'error', message: 'Job title and description (min 20 chars) are required.' });
      return;
    }
    setSaving(true);
    setMsg(null);
    try {
      const reqSkills = form.required_skills_text
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      const prefSkills = form.preferred_skills_text
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

      await api.createJob({
        title: form.title,
        department: form.department,
        description: form.description,
        required_skills: reqSkills,
        preferred_skills: prefSkills,
        min_experience_years: Number(form.min_experience_years) || 0,
        education_requirement: form.education_requirement,
        additional_qualifications: form.additional_qualifications,
        auto_extract: true,
      });
      setForm(EMPTY_FORM);
      setMsg({ type: 'success', message: 'Role requisition created and ready for screening.' });
      await loadJobs();
    } catch (e) {
      setMsg({ type: 'error', message: e.message });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.deleteJob(id);
      await loadJobs();
    } catch (e) {
      setMsg({ type: 'error', message: e.message });
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Job Requisitions"
        title="Open Roles & Requirements"
        subtitle="Create open positions or paste a job description to automatically populate required skills, preferred qualifications, and minimum experience."
      />

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Create Job Form */}
        <GlassCard className="p-6 lg:col-span-2">
          <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <Plus className="w-4 h-4 text-blue-400" />
            Create Open Role
          </h2>

          <form onSubmit={handleSave} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Role Title *</label>
                <input
                  type="text"
                  required
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="e.g. Senior ML Engineer"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-sm text-white focus:outline-none focus:border-blue-400"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Department</label>
                <input
                  type="text"
                  value={form.department}
                  onChange={(e) => setForm({ ...form, department: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-sm text-white focus:outline-none focus:border-blue-400"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-medium text-slate-300">Job Description *</label>
                <button
                  type="button"
                  onClick={handleAutoExtract}
                  disabled={analyzing}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-violet-300 hover:text-violet-200 disabled:opacity-50"
                >
                  <Wand2 className="w-3.5 h-3.5" />
                  {analyzing ? 'Extracting...' : 'Extract Requirements'}
                </button>
              </div>
              <textarea
                rows={5}
                required
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Paste job responsibilities, required skills, nice-to-have skills, experience, and degree requirements..."
                className="w-full px-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-sm text-white focus:outline-none focus:border-blue-400"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Required Skills (comma-separated)</label>
              <input
                type="text"
                value={form.required_skills_text}
                onChange={(e) => setForm({ ...form, required_skills_text: e.target.value })}
                placeholder="Python, Machine Learning, SQL"
                className="w-full px-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-sm text-white focus:outline-none focus:border-blue-400"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Preferred Skills (comma-separated)</label>
              <input
                type="text"
                value={form.preferred_skills_text}
                onChange={(e) => setForm({ ...form, preferred_skills_text: e.target.value })}
                placeholder="Docker, AWS, Git"
                className="w-full px-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-sm text-white focus:outline-none focus:border-blue-400"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Min Experience (Yrs)</label>
                <input
                  type="number"
                  min={0}
                  max={40}
                  step={0.5}
                  value={form.min_experience_years}
                  onChange={(e) => setForm({ ...form, min_experience_years: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-sm text-white focus:outline-none focus:border-blue-400"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Education Level</label>
                <select
                  value={form.education_requirement}
                  onChange={(e) => setForm({ ...form, education_requirement: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-sm text-white focus:outline-none focus:border-blue-400"
                >
                  <option value="Unspecified">Unspecified</option>
                  <option value="Diploma">Diploma</option>
                  <option value="Bachelor's">Bachelor's</option>
                  <option value="Master's">Master's</option>
                  <option value="PhD">PhD</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Additional Qualifications</label>
              <input
                type="text"
                value={form.additional_qualifications}
                onChange={(e) => setForm({ ...form, additional_qualifications: e.target.value })}
                placeholder="Certifications, domain experience, etc."
                className="w-full px-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-sm text-white focus:outline-none focus:border-blue-400"
              />
            </div>

            {msg && (
              <div
                className={`p-3 rounded-xl text-xs border ${
                  msg.type === 'success'
                    ? 'bg-emerald-500/10 border-emerald-400/30 text-emerald-200'
                    : 'bg-rose-500/10 border-rose-400/30 text-rose-200'
                }`}
              >
                {msg.message}
              </div>
            )}

            <button
              type="submit"
              disabled={saving}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 disabled:opacity-50 transition"
            >
              {saving ? 'Saving Role...' : 'Save Open Role'}
            </button>
          </form>
        </GlassCard>

        {/* Saved Jobs List */}
        <div className="lg:col-span-3 space-y-4">
          {loading ? (
            <LoadingSpinner label="Loading open roles..." />
          ) : jobs.length === 0 ? (
            <EmptyState
              icon={Briefcase}
              title="No open roles saved"
              description="Create your first job requisition using the form on the left."
            />
          ) : (
            jobs.map((job) => (
              <GlassCard key={job.id} hover className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-base font-semibold text-white">{job.title}</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      {job.department === 'Synthetic Demo' ? 'General' : job.department} • Min {job.min_experience_years} yrs •{' '}
                      {job.education_requirement}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDelete(job.id)}
                    className="p-1.5 rounded-lg bg-white/5 hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 transition"
                    title="Delete role"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <p className="text-xs text-slate-300 mt-3 line-clamp-2 leading-relaxed">{job.description}</p>

                <div className="mt-3 flex flex-wrap gap-1.5">
                  {(job.required_skills || []).map((sk) => (
                    <span
                      key={sk}
                      className="px-2 py-0.5 rounded-md bg-blue-500/15 border border-blue-400/25 text-blue-200 text-[11px] font-medium"
                    >
                      {sk}
                    </span>
                  ))}
                  {(job.preferred_skills || []).map((sk) => (
                    <span
                      key={sk}
                      className="px-2 py-0.5 rounded-md bg-violet-500/15 border border-violet-400/25 text-violet-200 text-[11px]"
                    >
                      +{sk}
                    </span>
                  ))}
                </div>
              </GlassCard>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
