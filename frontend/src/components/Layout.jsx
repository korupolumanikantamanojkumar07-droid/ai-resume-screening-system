import { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  BarChart3,
  Briefcase,
  EyeOff,
  FileSpreadsheet,
  Home,
  LayoutDashboard,
  Menu,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  UploadCloud,
  UserCheck,
  Users,
  X,
} from 'lucide-react';
import { api } from '../api';

const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: Home },
  { to: '/dashboard', label: 'HR Dashboard', icon: LayoutDashboard },
  { to: '/upload', label: 'Candidate Intake', icon: UploadCloud },
  { to: '/jobs', label: 'Open Roles', icon: Briefcase },
  { to: '/screening', label: 'Run Screening', icon: UserCheck },
  { to: '/results', label: 'Shortlist & Results', icon: Users },
  { to: '/analytics', label: 'Hiring Analytics', icon: BarChart3 },
  { to: '/reports', label: 'HR Reports', icon: FileSpreadsheet },
  { to: '/settings', label: 'Screening Settings', icon: SlidersHorizontal },
];

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [blindMode, setBlindMode] = useState(false);
  const [privacyCfg, setPrivacyCfg] = useState(null);

  useEffect(() => {
    api
      .getSettings()
      .then((res) => {
        if (res?.privacy_retention) {
          setPrivacyCfg(res.privacy_retention);
          setBlindMode(Boolean(res.privacy_retention.anonymize_candidates));
        }
      })
      .catch(() => {});
  }, []);

  const toggleBlindMode = async () => {
    const next = !blindMode;
    setBlindMode(next);
    try {
      const updated = {
        anonymize_candidates: next,
        mask_contact_info: privacyCfg?.mask_contact_info ?? true,
        file_retention_days: privacyCfg?.file_retention_days ?? 90,
      };
      await api.updatePrivacy(updated);
      setPrivacyCfg(updated);
      window.location.reload();
    } catch {
      setBlindMode(!next);
    }
  };

  const navContent = (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/10">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center shadow-lg shadow-blue-500/25 shrink-0">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="font-display font-bold text-sm text-white leading-tight">
            AI-Based Resume Screening System
          </div>
          <div className="text-[11px] text-slate-400">HR Talent Suite</div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-blue-600/25 to-violet-600/20 text-white border border-blue-400/30 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="p-4 m-3 rounded-xl bg-slate-900/80 border border-white/10 space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-300">
          <ShieldCheck className="w-4 h-4 shrink-0" />
          Fair Hiring Guardrail
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Evaluates skills, experience, and qualifications only. Personal demographics are strictly excluded.
        </p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#060B18] mesh-bg text-slate-100 flex">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0 bg-[#080E1E]/95 backdrop-blur-xl border-r border-white/10 z-30">
        {navContent}
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className="relative w-64 max-w-xs bg-[#080E1E] border-r border-white/10 h-full z-10">
            <button
              onClick={() => setMobileOpen(false)}
              className="absolute top-4 right-3 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10"
              aria-label="Close navigation"
            >
              <X className="w-5 h-5" />
            </button>
            {navContent}
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 lg:pl-64 flex flex-col min-w-0">
        <header className="sticky top-0 z-20 flex items-center justify-between px-4 sm:px-8 h-14 bg-[#060B18]/85 backdrop-blur-xl border-b border-white/10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 rounded-lg text-slate-300 hover:bg-white/10"
              aria-label="Open menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <span className="text-xs font-medium text-slate-400 hidden sm:inline">
              HR Talent Screening &amp; Decision-Support Workspace
            </span>
          </div>
          <div className="flex items-center gap-2.5">
            <button
              onClick={toggleBlindMode}
              title="Toggle Blind Screening (hides candidate names and contact details across views)"
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition ${
                blindMode
                  ? 'bg-violet-500/20 text-violet-200 border-violet-400/40'
                  : 'bg-white/5 text-slate-300 border-white/15 hover:bg-white/10'
              }`}
            >
              <EyeOff className="w-3.5 h-3.5" />
              {blindMode ? 'Blind Screening: ON' : 'Blind Screening: OFF'}
            </button>
          </div>
        </header>

        <main className="flex-1 px-4 sm:px-8 py-6 max-w-[1440px] w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
