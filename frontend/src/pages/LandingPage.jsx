import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  BarChart3,
  Briefcase,
  CheckCircle2,
  EyeOff,
  FileCheck2,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  Users,
} from 'lucide-react';
import { GlassCard } from '../components/UI';

const HR_CAPABILITIES = [
  {
    icon: UploadCloud,
    title: 'Fast Multi-Resume Intake',
    desc: 'Upload PDF and DOCX applicant resumes in bulk. Duplicate submissions are automatically detected and prevented.',
  },
  {
    icon: Briefcase,
    title: 'Smart Role Requirement Matching',
    desc: 'Paste any job description to extract required skills, preferred qualifications, experience, and degree criteria automatically.',
  },
  {
    icon: EyeOff,
    title: 'Blind Screening & Fair Evaluation',
    desc: 'One-click Blind Mode hides candidate names and contact details so shortlisting stays focused purely on merit and role fit.',
  },
  {
    icon: BarChart3,
    title: 'Hiring Analytics & Dossier Exports',
    desc: 'Explore skill gaps across applicant pools and download executive PDF dossiers or CSV shortlists for hiring managers.',
  },
];

const WORKFLOW_STEPS = [
  {
    step: '01',
    title: 'Upload Applicant CVs',
    desc: 'Drag and drop PDF or DOCX resumes into your private HR talent intake.',
  },
  {
    step: '02',
    title: 'Define Open Role Criteria',
    desc: 'Create job requisitions with must-have skills, experience, and education targets.',
  },
  {
    step: '03',
    title: 'Review & Shortlist Top Talent',
    desc: 'Compare transparent compatibility scores, matched vs. missing skills, and export reports.',
  },
];

export default function LandingPage() {
  return (
    <div className="space-y-10 pb-12">
      {/* Executive HR Hero */}
      <motion.section
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative overflow-hidden rounded-3xl glass-card p-8 sm:p-12 border border-blue-500/20"
      >
        <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full bg-blue-600/20 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-80 h-80 rounded-full bg-violet-600/20 blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/15 border border-blue-400/30 text-blue-300 text-xs font-semibold mb-5">
            <Sparkles className="w-3.5 h-3.5" />
            Intelligent Talent Screening for HR Teams
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Shortlist the{' '}
            <span className="bg-gradient-to-r from-blue-400 via-sky-300 to-violet-400 bg-clip-text text-transparent">
              Right Candidates
            </span>{' '}
            with Explainable AI
          </h1>

          <p className="mt-4 text-base sm:text-lg text-slate-300 leading-relaxed">
            Built for HR and talent acquisition teams to screen applicant resumes, evaluate role compatibility,
            protect candidate privacy, and deliver transparent shortlists to hiring managers.
          </p>

          <div className="mt-8 flex flex-wrap gap-3.5">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white font-semibold shadow-lg shadow-blue-600/25 transition"
            >
              Open HR Dashboard
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/upload"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/15 text-slate-200 font-medium transition"
            >
              <UploadCloud className="w-4 h-4 text-blue-400" />
              Upload Applicant CVs
            </Link>
            <Link
              to="/results"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/15 text-slate-200 font-medium transition"
            >
              <Users className="w-4 h-4 text-violet-400" />
              View Shortlist
            </Link>
          </div>
        </div>
      </motion.section>

      {/* Capabilities */}
      <section>
        <h2 className="text-xl font-bold text-white mb-4">Everything Your Hiring Team Needs</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {HR_CAPABILITIES.map((item, idx) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.06 }}
              >
                <GlassCard hover className="p-6 h-full">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 border border-blue-400/25 flex items-center justify-center text-blue-300 mb-4">
                    <Icon className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{item.desc}</p>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* 3-Step Workflow + Governance */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <GlassCard className="p-6 sm:p-8 lg:col-span-2">
          <h2 className="text-xl font-bold text-white mb-5">3-Step Screening Workflow</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {WORKFLOW_STEPS.map((w) => (
              <div key={w.step} className="p-4 rounded-xl bg-slate-900/70 border border-white/10 space-y-2">
                <span className="inline-flex w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-400/30 text-blue-300 font-mono text-xs font-bold items-center justify-center">
                  {w.step}
                </span>
                <div className="text-sm font-semibold text-white">{w.title}</div>
                <p className="text-xs text-slate-400 leading-relaxed">{w.desc}</p>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard className="p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-emerald-300 font-semibold text-sm mb-3">
              <ShieldCheck className="w-5 h-5" />
              HR Governance &amp; Privacy
            </div>
            <ul className="space-y-2.5 text-xs text-slate-300">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>Candidate emails and phone numbers are masked by default.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>Zero protected demographics used in candidate scoring.</span>
              </li>
              <li className="flex items-start gap-2">
                <FileCheck2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>Every ranking provides clear matched and missing skills.</span>
              </li>
            </ul>
          </div>
          <Link
            to="/settings"
            className="mt-5 inline-flex items-center justify-center py-2.5 px-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/15 text-xs font-medium text-white transition"
          >
            Configure Privacy &amp; Weights
          </Link>
        </GlassCard>
      </div>
    </div>
  );
}
