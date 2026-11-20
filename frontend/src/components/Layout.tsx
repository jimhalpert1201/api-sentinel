import { useState, FC } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Activity,
  Bell,
  LogOut,
  Radio,
  ShieldCheck,
  User as UserIcon,
  Menu,
  X,
  LayoutDashboard,
  Cpu,
} from 'lucide-react';

export const Layout: FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  // Determine current page title
  const getPageTitle = () => {
    if (location.pathname === '/') return 'System Overview';
    if (location.pathname.startsWith('/monitors/')) return 'Monitor Telemetry';
    if (location.pathname === '/incidents') return 'Incident Management';
    return 'Dashboard';
  };

  const navItems = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/incidents', label: 'Incidents', icon: Bell },
  ];

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex font-sans antialiased">
      {/* Mobile Drawer Backdrop */}
      {mobileMenuOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar (Desktop Persistent, Mobile Drawer) */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-[#0e1526] border-r border-slate-800/80 flex flex-col justify-between transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div>
          {/* Brand Logo & Name */}
          <div className="h-16 flex items-center justify-between px-6 border-b border-slate-800/80">
            <NavLink
              to="/"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-3 group"
            >
              <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center transition-all group-hover:scale-105 group-hover:border-emerald-500/40 shadow-inner">
                <Activity className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-sm tracking-tight text-white group-hover:text-emerald-400 transition-colors">
                  API SENTINEL
                </span>
                <span className="text-[10px] text-slate-400 uppercase tracking-widest font-mono">
                  Observability SaaS
                </span>
              </div>
            </NavLink>

            {/* Mobile close button */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(false)}
              className="p-1 rounded-lg text-slate-400 hover:text-white lg:hidden"
              aria-label="Close navigation"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <div className="px-4 py-6 space-y-1">
            <div className="px-3 pb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
              Platform
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm font-semibold'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </div>
        </div>

        {/* Sidebar Footer: Monitoring Engine Status & Version */}
        <div className="p-4 border-t border-slate-800/80 space-y-3">
          <div className="p-3 rounded-xl bg-[#080d19] border border-slate-800/90 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400 flex items-center gap-1.5 font-medium">
                <Cpu className="w-3.5 h-3.5 text-emerald-400" />
                Monitoring
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                ACTIVE
              </span>
            </div>
            <div className="text-[11px] text-slate-400 flex items-center justify-between font-mono">
              <span>Async Engine</span>
              <span>v0.3.0</span>
            </div>
          </div>

          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-[11px] text-slate-400">Zero-Celery Cloud</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        {/* Top Header */}
        <header className="sticky top-0 z-40 h-16 bg-[#0e1526]/80 border-b border-slate-800/80 backdrop-blur-md px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open navigation menu"
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 lg:hidden"
            >
              <Menu className="w-5 h-5" />
            </button>

            <div>
              <h1 className="text-sm sm:text-base font-bold text-white tracking-tight">
                {getPageTitle()}
              </h1>
            </div>
          </div>

          {/* Right Header: Live Status + User profile + Logout */}
          <div className="flex items-center gap-3">
            {/* Live Indicator Pill */}
            <div className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono font-medium">
              <Radio className="w-3.5 h-3.5 animate-pulse" />
              <span>LIVE TELEMETRY</span>
            </div>

            {/* User Profile info */}
            <div className="flex items-center gap-2 pl-2">
              <div className="w-8 h-8 rounded-xl bg-slate-800/90 border border-slate-700/80 text-emerald-400 flex items-center justify-center text-xs font-semibold">
                <UserIcon className="w-4 h-4" />
              </div>
              <div className="hidden md:flex flex-col text-left">
                <span className="text-xs font-semibold text-slate-200">{user?.username}</span>
                <span className="text-[10px] text-slate-400 truncate max-w-[120px]">{user?.email}</span>
              </div>
            </div>

            {/* Logout Button */}
            <button
              type="button"
              onClick={handleLogout}
              aria-label="Sign out"
              title="Sign out"
              className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>

        {/* Bottom Status Footer */}
        <footer className="border-t border-slate-800/60 py-4 px-6 text-xs text-slate-400">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
            <span className="font-mono text-[11px]">API Sentinel Observability Platform</span>
            <span className="text-[11px] text-slate-400">
              In-Memory Token Rotation & Multi-Tenant Isolated
            </span>
          </div>
        </footer>
      </div>
    </div>
  );
};
