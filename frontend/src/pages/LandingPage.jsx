import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  Brain,
  CheckCircle2,
  Cpu,
  Database,
  FileSearch,
  Layers,
  Scale,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { api } from '../api';
import { GlassCard } from '../components/UI';

const FEATURES = [
  {
    icon: FileSearch,
    title: 'Multi-Format & OCR Extraction',
    desc: 'Parses PDF and DOCX resumes via PyMuPDF and python-docx with automatic OCR fallback for scanned PDFs and SHA-256 duplicate detection.',
  },
  {
    icon: Brain,
    title: 'spaCy NER & Synonym Taxonomy',
    desc: 'Extracts candidate entities, degrees, experience timelines, projects, certifications, and normalizes skill synonyms like ML → Machine Learning.',
  },
  {
    icon: Sparkles,
    title: 'Sentence Transformer Semantics',
    desc: 'Uses all-MiniLM-L6-v2 dense embeddings and TF-IDF cosine similarity to understand contextual fit beyond literal keyword matching.',
  },
  {
    icon: Scale,
    title: 'Explainable & Fair Ranking',
    desc: 'Deterministic weighted scoring (35% skills, 25% semantics, 20% experience, 10% education, 10% preferred) with zero protected attributes.',
  },
];

const PIPELINE_STEPS = [
  'PDF / DOCX / Dataset Ingestion',
  'Text Cleaning & Lemmatization',
  'spaCy NER & Section Parsing',
  'Taxonomy + Semantic Skill Match',
  'MiniLM Embeddings & TF-IDF',
  'Weighted Deterministic Ranking',
];

const TECH_STACK = [
  'React.js + Tailwind CSS',
  'Framer Motion + Recharts',
  'FastAPI + SQLAlchemy',
  'spaCy (en_core_web_sm)',
  'Sentence Transformers (all-MiniLM-L6-v2)',
  'Scikit-learn TF-IDF + NLTK',
  'PyMuPDF + RapidOCR + python-docx',
  'SQLite + ReportLab PDF',
];

export default function LandingPage() {
  const [datasetsInfo, setDatasetsInfo] = useState([]);

  useEffect(() => {
    fetch(`${api.getBaseUrl()}/settings/datasets/inspect`)
      .then((r) => (r.ok ? r.json() : { datasets: [] }))
      .then((d) => setDatasetsInfo(d.datasets || []))
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-12 pb-12">
      {/* Hero Section */}
      <motion.section
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
        className="relative overflow-hidden rounded-3xl glass-card p-8 sm:p-12 border border-blue-500/20"
      >
        <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full bg-blue-600/20 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-80 h-80 rounded-full bg-violet-600/20 blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/15 border border-blue-400/30 text-blue-300 text-xs font-semibold mb-5">
            <Cpu className="w-3.5 h-3.5" />
            Real NLP Pipeline • Sentence Transformers • Kaggle Datasets
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Intelligent{' '}
            <span className="bg-gradient-to-r from-blue-400 via-sky-300 to-violet-400 bg-clip-text text-transparent">
              AI-Based Resume Screening
            </span>{' '}
            &amp; Explainable Candidate Ranking
          </h1>

          <p className="mt-4 text-base sm:text-lg text-slate-300 leading-relaxed">
            Automate resume parsing, semantic skill extraction, and candidate-job compatibility scoring using
            spaCy NER, <code className="text-blue-300 bg-blue-950/60 px-1.5 py-0.5 rounded text-sm">all-MiniLM-L6-v2</code>{' '}
            embeddings, TF-IDF vectorization, and transparent multi-criteria ranking.
          </p>

          <div className="mt-8 flex flex-wrap gap-3.5">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white font-semibold shadow-lg shadow-blue-600/25 transition"
            >
              Get Started
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/upload"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/15 text-slate-200 font-medium transition"
            >
              Upload Resumes
            </Link>
            <Link
              to="/settings"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/15 text-slate-200 font-medium transition"
            >
              Load Kaggle Datasets
            </Link>
          </div>
        </div>
      </motion.section>

      {/* Main Features */}
      <section>
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Layers className="w-5 h-5 text-blue-400" />
          Core Platform Capabilities
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {FEATURES.map((f, i) => {
            const Icon = f.icon;
            return (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
              >
                <GlassCard hover className="p-6 h-full">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 border border-blue-400/25 flex items-center justify-center text-blue-300 mb-4">
                    <Icon className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">{f.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* How It Works */}
      <section>
        <GlassCard className="p-6 sm:p-8">
          <h2 className="text-xl font-bold text-white mb-5">How the NLP Pipeline Works</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {PIPELINE_STEPS.map((step, idx) => (
              <div
                key={step}
                className="flex items-center gap-3 p-4 rounded-xl bg-slate-900/70 border border-white/10"
              >
                <span className="w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-400/30 text-blue-300 font-mono text-sm font-bold flex items-center justify-center shrink-0">
                  0{idx + 1}
                </span>
                <span className="text-sm font-medium text-slate-200">{step}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </section>

      {/* Dataset Integration & Tech Stack */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <GlassCard className="p-6 lg:col-span-2">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-violet-400" />
            Integrated Public Kaggle Datasets
          </h2>
          <div className="space-y-3">
            {datasetsInfo.map((ds) => (
              <div
                key={ds.key}
                className="p-4 rounded-xl bg-slate-900/70 border border-white/10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
              >
                <div>
                  <div className="font-semibold text-white text-sm">{ds.name}</div>
                  <div className="text-xs text-slate-400 mt-0.5 break-all">{ds.url}</div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {ds.exists ? (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs bg-emerald-500/15 text-emerald-300 border border-emerald-400/30">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      {ds.row_count} raw records verified
                    </span>
                  ) : (
                    <span className="text-xs text-amber-300">Not downloaded yet</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard className="p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            Technology Stack
          </h2>
          <div className="flex flex-wrap gap-2">
            {TECH_STACK.map((t) => (
              <span
                key={t}
                className="px-3 py-1.5 rounded-lg bg-slate-900/80 border border-white/10 text-xs font-medium text-slate-300"
              >
                {t}
              </span>
            ))}
          </div>
          <p className="mt-4 text-xs text-slate-400 leading-relaxed">
            Built for transparent decision-support: protected characteristics (age, gender, religion, caste,
            nationality, photos) are strictly excluded from scoring.
          </p>
        </GlassCard>
      </div>
    </div>
  );
}
