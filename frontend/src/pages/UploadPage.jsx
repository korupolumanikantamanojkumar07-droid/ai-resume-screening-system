import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  RefreshCw,
  Search,
  Trash2,
  UploadCloud,
} from 'lucide-react';
import { api } from '../api';
import { EmptyState, GlassCard, LoadingSpinner, PageHeader, SourceBadge, StatusBadge } from '../components/UI';

export default function UploadPage() {
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [sourceFilter, setSourceFilter] = useState('all');
  const [search, setSearch] = useState('');
  const fileInputRef = useRef(null);
  const replaceInputRef = useRef(null);
  const [replaceTargetId, setReplaceTargetId] = useState(null);

  const loadResumes = async () => {
    setLoading(true);
    try {
      const res = await api.listResumes({ source_type: sourceFilter, search });
      setResumes(res.items || []);
    } catch (e) {
      setFeedback({ type: 'error', message: e.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResumes();
  }, [sourceFilter]);

  const validateAndUpload = async (fileList) => {
    const files = Array.from(fileList || []);
    if (!files.length) return;

    const valid = [];
    const clientErrors = [];
    for (const f of files) {
      const ext = f.name.slice(f.name.lastIndexOf('.')).toLowerCase();
      if (!['.pdf', '.docx'].includes(ext)) {
        clientErrors.push(`${f.name}: unsupported format (only PDF/DOCX allowed)`);
      } else if (f.size > 10 * 1024 * 1024) {
        clientErrors.push(`${f.name}: exceeds 10 MB limit`);
      } else {
        valid.push(f);
      }
    }

    if (!valid.length) {
      setFeedback({ type: 'error', message: clientErrors.join(' | ') });
      return;
    }

    setUploading(true);
    setUploadProgress(25);
    setFeedback(null);
    const timer = setInterval(() => {
      setUploadProgress((p) => (p < 85 ? p + 10 : p));
    }, 350);

    try {
      const res = await api.uploadResumes(valid);
      clearInterval(timer);
      setUploadProgress(100);
      const msgs = [];
      if (res.uploaded_count > 0) msgs.push(`Processed ${res.uploaded_count} resume(s) through NLP pipeline.`);
      const allErrors = [...clientErrors, ...(res.errors || []).map((e) => `${e.filename}: ${e.error}`)];
      if (allErrors.length) msgs.push(`Warnings: ${allErrors.join(' | ')}`);

      setFeedback({
        type: res.uploaded_count > 0 && !allErrors.length ? 'success' : res.uploaded_count > 0 ? 'warning' : 'error',
        message: msgs.join(' '),
      });
      await loadResumes();
    } catch (e) {
      clearInterval(timer);
      setFeedback({ type: 'error', message: e.message });
    } finally {
      setTimeout(() => {
        setUploading(false);
        setUploadProgress(0);
      }, 450);
    }
  };

  const handleReplaceFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !replaceTargetId) return;
    setUploading(true);
    try {
      await api.replaceResume(replaceTargetId, file);
      setFeedback({ type: 'success', message: `Replaced resume with ${file.name} and re-ran NLP extraction.` });
      await loadResumes();
    } catch (err) {
      setFeedback({ type: 'error', message: err.message });
    } finally {
      setUploading(false);
      setReplaceTargetId(null);
      e.target.value = '';
    }
  };

  const handleDelete = async (id, filename) => {
    try {
      await api.deleteResume(id);
      setFeedback({ type: 'success', message: `Removed '${filename}'.` });
      await loadResumes();
    } catch (err) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Step 1 • Extraction & NER"
        title="Resume Upload & Pool"
        subtitle="Upload multiple PDF or DOCX resumes. Scanned PDFs automatically trigger OCR, and SHA-256 hashing prevents duplicates."
      />

      {/* Drag & Drop Zone */}
      <GlassCard className="p-6">
        <motion.div
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            validateAndUpload(e.dataTransfer.files);
          }}
          whileHover={{ scale: 1.003 }}
          className={`border-2 border-dashed rounded-2xl p-8 sm:p-10 text-center transition-all cursor-pointer ${
            dragActive
              ? 'border-blue-400 bg-blue-500/10'
              : 'border-white/15 bg-slate-900/40 hover:border-blue-400/50'
          }`}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx"
            className="hidden"
            onChange={(e) => {
              validateAndUpload(e.target.files);
              e.target.value = '';
            }}
          />
          <input
            ref={replaceInputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={handleReplaceFile}
          />
          <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 border border-blue-400/30 flex items-center justify-center text-blue-300 mb-4">
            <UploadCloud className="w-7 h-7" />
          </div>
          <h3 className="text-lg font-semibold text-white">Drop PDF or DOCX resumes here, or click to browse</h3>
          <p className="text-sm text-slate-400 mt-1">
            Supports multi-file upload (max 10 MB per file). Runs PyMuPDF / OCR + spaCy NER + MiniLM embeddings.
          </p>

          {uploading && (
            <div className="mt-6 max-w-md mx-auto">
              <div className="flex justify-between text-xs text-blue-300 mb-1.5">
                <span>Extracting &amp; running NLP pipeline...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-violet-500 transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}
        </motion.div>

        {feedback && (
          <div
            className={`mt-4 p-3.5 rounded-xl border text-sm flex items-start gap-2.5 ${
              feedback.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-400/30 text-emerald-200'
                : feedback.type === 'warning'
                ? 'bg-amber-500/10 border-amber-400/30 text-amber-200'
                : 'bg-rose-500/10 border-rose-400/30 text-rose-200'
            }`}
          >
            {feedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
            )}
            <span>{feedback.message}</span>
          </div>
        )}
      </GlassCard>

      {/* Filter Bar & Uploaded List */}
      <GlassCard className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
          <div className="flex flex-wrap items-center gap-2">
            {['all', 'uploaded', 'synthetic_demo', 'public_dataset'].map((src) => (
              <button
                key={src}
                onClick={() => setSourceFilter(src)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                  sourceFilter === src
                    ? 'bg-blue-600/25 border-blue-400/40 text-white'
                    : 'bg-white/5 border-white/10 text-slate-400 hover:text-white'
                }`}
              >
                {src === 'all'
                  ? 'All Resumes'
                  : src === 'uploaded'
                  ? 'Uploaded Only'
                  : src === 'synthetic_demo'
                  ? 'Synthetic Demo'
                  : 'Public Dataset'}
              </button>
            ))}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              loadResumes();
            }}
            className="flex items-center gap-2"
          >
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search filename, name, category..."
                className="pl-9 pr-3 py-1.5 rounded-xl bg-slate-900/80 border border-white/10 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-400"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/15 text-xs font-medium text-white"
            >
              Search
            </button>
          </form>
        </div>

        {loading ? (
          <LoadingSpinner label="Fetching processed resumes..." />
        ) : resumes.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No resumes found"
            description="Upload PDF/DOCX resumes above or load the Kaggle datasets in Settings & Datasets."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-white/10 text-xs text-slate-400">
                  <th className="py-2.5 pr-3">Candidate / File</th>
                  <th className="py-2.5 pr-3">Source</th>
                  <th className="py-2.5 pr-3">Skills Extracted</th>
                  <th className="py-2.5 pr-3">Exp</th>
                  <th className="py-2.5 pr-3">Education</th>
                  <th className="py-2.5 pr-3">Status</th>
                  <th className="py-2.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {resumes.map((r) => (
                  <tr key={r.id} className="hover:bg-white/5 transition">
                    <td className="py-3 pr-3">
                      <div className="font-medium text-white">
                        {r.candidate_id ? (
                          <Link to={`/candidates/${r.candidate_id}`} className="hover:text-blue-400">
                            {r.candidate_name || r.filename}
                          </Link>
                        ) : (
                          r.filename
                        )}
                      </div>
                      <div className="text-xs text-slate-400 flex items-center gap-2">
                        <span>{r.filename}</span>
                        {r.ocr_used && (
                          <span className="px-1.5 py-0.2 rounded bg-amber-500/15 text-amber-300 text-[10px]">OCR</span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 pr-3">
                      <SourceBadge sourceType={r.source_type} />
                      {r.dataset_category && r.source_type === 'public_dataset' && (
                        <div className="text-[11px] text-slate-400 mt-1">{r.dataset_category}</div>
                      )}
                    </td>
                    <td className="py-3 pr-3">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {(r.skills_preview || []).map((sk) => (
                          <span
                            key={sk}
                            className="px-2 py-0.5 rounded-md bg-blue-500/10 border border-blue-400/20 text-blue-200 text-[11px]"
                          >
                            {sk}
                          </span>
                        ))}
                        {r.skills_count > 6 && (
                          <span className="text-[11px] text-slate-400">+{r.skills_count - 6}</span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 pr-3 font-mono text-xs text-slate-300">{r.experience_years} yrs</td>
                    <td className="py-3 pr-3 text-xs text-slate-300">{r.education_level}</td>
                    <td className="py-3 pr-3">
                      <StatusBadge status={r.processing_status} />
                    </td>
                    <td className="py-3 text-right">
                      <div className="inline-flex items-center gap-1.5">
                        {r.source_type === 'uploaded' && (
                          <button
                            title="Replace file"
                            onClick={() => {
                              setReplaceTargetId(r.id);
                              replaceInputRef.current?.click();
                            }}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-blue-500/20 text-slate-300 hover:text-blue-300 transition"
                          >
                            <RefreshCw className="w-3.5 h-3.5" />
                          </button>
                        )}
                        <button
                          title="Delete resume"
                          onClick={() => handleDelete(r.id, r.filename)}
                          className="p-1.5 rounded-lg bg-white/5 hover:bg-rose-500/20 text-slate-300 hover:text-rose-300 transition"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
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
