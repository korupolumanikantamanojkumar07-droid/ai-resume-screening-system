import { useEffect, useState } from 'react';
import { Database, Plus, Save, Shield, Sliders, Trash2 } from 'lucide-react';
import { api } from '../api';
import { GlassCard, LoadingSpinner, PageHeader } from '../components/UI';

export default function SettingsPage() {
  const [settingsData, setSettingsData] = useState(null);
  const [weights, setWeights] = useState(null);
  const [privacy, setPrivacy] = useState(null);
  const [newSkill, setNewSkill] = useState({ name: '', category: 'AI/ML', synonyms: '' });
  const [datasetCfg, setDatasetCfg] = useState({ resume_limit: 40, ner_limit: 20, jobs_limit: 10 });
  const [loading, setLoading] = useState(true);
  const [loadingDatasets, setLoadingDatasets] = useState(false);
  const [msg, setMsg] = useState(null);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const res = await api.getSettings();
      setSettingsData(res);
      setWeights(res.scoring_weights);
      setPrivacy(res.privacy_retention);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  if (loading || !weights || !privacy) return <LoadingSpinner label="Loading platform configuration..." />;

  const weightSum = Object.values(weights).reduce((a, b) => a + Number(b || 0), 0);

  const saveWeights = async () => {
    if (Math.abs(weightSum - 100) > 0.01) {
      setMsg({ type: 'error', message: `Weights must sum to 100% (currently ${weightSum.toFixed(1)}%).` });
      return;
    }
    try {
      await api.updateWeights(weights);
      setMsg({ type: 'success', message: 'Scoring weights updated.' });
    } catch (e) {
      setMsg({ type: 'error', message: e.message });
    }
  };

  const savePrivacy = async () => {
    try {
      await api.updatePrivacy(privacy);
      setMsg({ type: 'success', message: 'Privacy & file retention settings saved.' });
    } catch (e) {
      setMsg({ type: 'error', message: e.message });
    }
  };

  const handleAddSkill = async (e) => {
    e.preventDefault();
    if (!newSkill.name.trim()) return;
    try {
      await api.addSkill({
        name: newSkill.name.trim(),
        category: newSkill.category,
        synonyms: newSkill.synonyms.split(',').map((s) => s.trim()).filter(Boolean),
      });
      setNewSkill({ name: '', category: 'AI/ML', synonyms: '' });
      setMsg({ type: 'success', message: 'Added skill to taxonomy.' });
      await loadSettings();
    } catch (e) {
      setMsg({ type: 'error', message: e.message });
    }
  };

  const handleLoadDatasets = async () => {
    setLoadingDatasets(true);
    setMsg(null);
    try {
      const res = await api.loadDatasets({ ...datasetCfg, clear_existing_dataset: false });
      const summaryText = (res.batches || [])
        .map((b) => `${b.dataset}: +${b.newly_loaded} new (${b.total_in_db} total)`)
        .join(' | ');
      setMsg({ type: 'success', message: `Kaggle datasets ingested! ${summaryText}` });
      await loadSettings();
    } catch (e) {
      setMsg({ type: 'error', message: e.message });
    } finally {
      setLoadingDatasets(false);
    }
  };

  const handleLoadInitialDemo = async () => {
    setLoadingDatasets(true);
    setMsg(null);
    try {
      const res = await api.loadInitialDemo();
      setMsg({
        type: 'success',
        message: `Initial synthetic demo dataset loaded: +${res.candidates_loaded} candidates, +${res.jobs_loaded} jobs (${res.total_demo_resumes_in_db} total in DB).`,
      });
      await loadSettings();
    } catch (e) {
      setMsg({ type: 'error', message: e.message });
    } finally {
      setLoadingDatasets(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Configuration & Kaggle Datasets"
        title="Settings & Dataset Pipeline"
        subtitle="Configure deterministic scoring weights, manage the skill taxonomy, control candidate privacy/retention, and load the Kaggle datasets."
      />

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

      {/* Scoring Weights & Privacy */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-blue-400" />
              Scoring Weight Configuration
            </h2>
            <span className={`text-xs font-mono ${Math.abs(weightSum - 100) < 0.01 ? 'text-emerald-300' : 'text-rose-300'}`}>
              Total: {weightSum.toFixed(0)}%
            </span>
          </div>

          {Object.entries(weights).map(([key, val]) => (
            <div key={key}>
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span className="capitalize">{key.replace('_', ' ')}</span>
                <span className="font-mono">{val}%</span>
              </div>
              <input
                type="range"
                min={0}
                max={100}
                step={5}
                value={val}
                onChange={(e) => setWeights({ ...weights, [key]: Number(e.target.value) })}
                className="w-full accent-blue-500"
              />
            </div>
          ))}

          <button
            onClick={saveWeights}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white"
          >
            <Save className="w-3.5 h-3.5" />
            Save Scoring Weights
          </button>
        </GlassCard>

        <GlassCard className="p-6 space-y-4">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-400" />
            Privacy &amp; File Retention
          </h2>

          <label className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-white/10 cursor-pointer">
            <div>
              <div className="text-xs font-medium text-white">Blind Review (Anonymize Names)</div>
              <div className="text-[11px] text-slate-400">Display Anonymous IDs (CND-XXXX) instead of candidate names</div>
            </div>
            <input
              type="checkbox"
              checked={privacy.anonymize_candidates}
              onChange={(e) => setPrivacy({ ...privacy, anonymize_candidates: e.target.checked })}
            />
          </label>

          <label className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-white/10 cursor-pointer">
            <div>
              <div className="text-xs font-medium text-white">Mask Contact Information</div>
              <div className="text-[11px] text-slate-400">Mask email addresses and phone numbers in API responses</div>
            </div>
            <input
              type="checkbox"
              checked={privacy.mask_contact_info}
              onChange={(e) => setPrivacy({ ...privacy, mask_contact_info: e.target.checked })}
            />
          </label>

          <div>
            <label className="block text-xs text-slate-300 mb-1">Uploaded File Retention (Days)</label>
            <input
              type="number"
              min={1}
              max={3650}
              value={privacy.file_retention_days}
              onChange={(e) => setPrivacy({ ...privacy, file_retention_days: Number(e.target.value) || 90 })}
              className="w-36 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-white"
            />
          </div>

          <button
            onClick={savePrivacy}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white"
          >
            <Save className="w-3.5 h-3.5" />
            Save Privacy Settings
          </button>
        </GlassCard>
      </div>

      {/* Kaggle Dataset Loader & Inspection */}
      <GlassCard className="p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Database className="w-4 h-4 text-violet-400" />
              Public Kaggle Dataset Loader &amp; Quality Inspection
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Loads real cleaned records into SQLite with <code className="text-violet-300">source_type=public_dataset</code>.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleLoadInitialDemo}
              disabled={loadingDatasets}
              className="px-4 py-2 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 border border-amber-400/30 text-xs font-semibold text-amber-200 disabled:opacity-50"
            >
              Load Initial Demo CSV
            </button>
            <button
              onClick={handleLoadDatasets}
              disabled={loadingDatasets}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-violet-600 text-xs font-semibold text-white disabled:opacity-50"
            >
              {loadingDatasets ? 'Ingesting & Running NLP...' : 'Load / Sync Public Datasets'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Resume Dataset Sample Size</label>
            <input
              type="number"
              min={10}
              max={500}
              value={datasetCfg.resume_limit}
              onChange={(e) => setDatasetCfg({ ...datasetCfg, resume_limit: Number(e.target.value) || 40 })}
              className="w-full px-3 py-1.5 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-white"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">NER Dataset Sample Size</label>
            <input
              type="number"
              min={5}
              max={220}
              value={datasetCfg.ner_limit}
              onChange={(e) => setDatasetCfg({ ...datasetCfg, ner_limit: Number(e.target.value) || 20 })}
              className="w-full px-3 py-1.5 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-white"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Job Descriptions Sample Size</label>
            <input
              type="number"
              min={5}
              max={100}
              value={datasetCfg.jobs_limit}
              onChange={(e) => setDatasetCfg({ ...datasetCfg, jobs_limit: Number(e.target.value) || 10 })}
              className="w-full px-3 py-1.5 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-white"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
          {(settingsData.raw_dataset_inspection?.datasets || []).map((ds) => {
            const loadedBatch = (settingsData.dataset_batches || []).find((b) => b.dataset_key === ds.key);
            const handleLoadInitialDemo = async () => {
    setLoadingDatasets(true);
    setMsg(null);
    try {
      const res = await api.loadInitialDemo();
      setMsg({
        type: 'success',
        message: `Initial synthetic demo dataset loaded: +${res.candidates_loaded} candidates, +${res.jobs_loaded} jobs (${res.total_demo_resumes_in_db} total in DB).`,
      });
      await loadSettings();
    } catch (e) {
      setMsg({ type: 'error', message: e.message });
    } finally {
      setLoadingDatasets(false);
    }
  };

  return (
              <div key={ds.key} className="p-4 rounded-xl bg-slate-900/70 border border-white/10 text-xs space-y-1.5">
                <div className="font-semibold text-white">{ds.name}</div>
                <div className="text-slate-400">Raw Rows: {ds.row_count ?? 0} • Duplicates: {ds.duplicate_count ?? 0}</div>
                <div className="text-slate-400">Columns: {(ds.columns || []).join(', ')}</div>
                <div className="text-emerald-300 font-medium">
                  Loaded in DB: {loadedBatch ? loadedBatch.loaded_count : 0}
                </div>
              </div>
            );
          })}
        </div>
      </GlassCard>

      {/* Skill Taxonomy Management */}
      <GlassCard className="p-6 space-y-4">
        <h2 className="text-base font-semibold text-white">Skill Taxonomy Management ({settingsData.skills_taxonomy.length} skills)</h2>
        <form onSubmit={handleAddSkill} className="flex flex-wrap gap-2">
          <input
            type="text"
            placeholder="Skill name (e.g. LangGraph)"
            value={newSkill.name}
            onChange={(e) => setNewSkill({ ...newSkill, name: e.target.value })}
            className="px-3 py-1.5 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-white"
          />
          <select
            value={newSkill.category}
            onChange={(e) => setNewSkill({ ...newSkill, category: e.target.value })}
            className="px-3 py-1.5 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-white"
          >
            <option value="Programming">Programming</option>
            <option value="AI/ML">AI/ML</option>
            <option value="Data">Data</option>
            <option value="Web">Web</option>
            <option value="Cloud">Cloud</option>
            <option value="DevOps">DevOps</option>
            <option value="Database">Database</option>
            <option value="Soft Skills">Soft Skills</option>
            <option value="Domain">Domain</option>
          </select>
          <input
            type="text"
            placeholder="Synonyms (comma-separated)"
            value={newSkill.synonyms}
            onChange={(e) => setNewSkill({ ...newSkill, synonyms: e.target.value })}
            className="flex-1 min-w-[200px] px-3 py-1.5 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-white"
          />
          <button
            type="submit"
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white"
          >
            <Plus className="w-3.5 h-3.5" /> Add Skill
          </button>
        </form>

        <div className="max-h-60 overflow-y-auto flex flex-wrap gap-1.5 pt-2">
          {settingsData.skills_taxonomy.map((sk) => (
            <div
              key={sk.id}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900/80 border border-white/10 text-xs text-slate-200"
            >
              <span>{sk.name}</span>
              <span className="text-[10px] text-slate-400">({sk.category})</span>
              {sk.is_custom && (
                <button
                  onClick={async () => {
                    await api.deleteSkill(sk.id);
                    await loadSettings();
                  }}
                  className="text-rose-400 hover:text-rose-300"
                  title="Remove custom skill"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              )}
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}
