import { motion } from 'framer-motion';

export function GlassCard({ children, className = '', hover = false, ...props }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`glass-card rounded-2xl ${hover ? 'glass-card-hover' : ''} ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );
}

export function PageHeader({ title, subtitle, badge, actions }) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        {badge && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/15 text-blue-300 border border-blue-400/25 mb-2">
            {badge}
          </span>
        )}
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">{title}</h1>
        {subtitle && <p className="text-sm text-slate-400 mt-1 max-w-2xl">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2.5">{actions}</div>}
    </div>
  );
}

export function ScoreBadge({ score }) {
  const val = Number(score || 0);
  let cls = 'bg-rose-500/15 text-rose-300 border-rose-400/30';
  if (val >= 75) cls = 'bg-emerald-500/15 text-emerald-300 border-emerald-400/30';
  else if (val >= 55) cls = 'bg-blue-500/15 text-blue-300 border-blue-400/30';
  else if (val >= 35) cls = 'bg-amber-500/15 text-amber-300 border-amber-400/30';

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold border ${cls}`}>
      {val.toFixed(1)}%
    </span>
  );
}

export function SourceBadge({ sourceType }) {
  const map = {
    public_dataset: {
      cls: 'bg-violet-500/15 text-violet-300 border-violet-400/30',
      label: 'Public Dataset',
    },
    synthetic_demo: {
      cls: 'bg-amber-500/15 text-amber-300 border-amber-400/30',
      label: 'Synthetic Demo',
    },
    uploaded: {
      cls: 'bg-sky-500/15 text-sky-300 border-sky-400/30',
      label: 'Uploaded Resume',
    },
  };
  const cfg = map[sourceType] || map.uploaded;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium border ${cfg.cls}`}>
      {cfg.label}
    </span>
  );
}

export function StatusBadge({ status }) {
  const map = {
    shortlisted: 'bg-emerald-500/15 text-emerald-300 border-emerald-400/30',
    review: 'bg-amber-500/15 text-amber-300 border-amber-400/30',
    rejected: 'bg-rose-500/15 text-rose-300 border-rose-400/30',
    screened: 'bg-blue-500/15 text-blue-300 border-blue-400/30',
    completed: 'bg-emerald-500/15 text-emerald-300 border-emerald-400/30',
    active: 'bg-emerald-500/15 text-emerald-300 border-emerald-400/30',
  };
  const cls = map[status] || 'bg-slate-500/15 text-slate-300 border-slate-400/30';
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize border ${cls}`}>
      {status}
    </span>
  );
}

export function LoadingSpinner({ label = 'Processing...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-14 gap-3 text-slate-400">
      <div className="w-8 h-8 rounded-full border-2 border-blue-500/30 border-t-blue-400 animate-spin" />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="glass-card rounded-2xl p-10 text-center flex flex-col items-center justify-center gap-3">
      {Icon && (
        <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-400/20 flex items-center justify-center text-blue-400">
          <Icon className="w-6 h-6" />
        </div>
      )}
      <h3 className="text-base font-semibold text-white">{title}</h3>
      {description && <p className="text-sm text-slate-400 max-w-md">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
