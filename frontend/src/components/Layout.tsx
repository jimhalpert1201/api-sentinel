import { FC } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Activity, Bell, LogOut, ShieldCheck, User as UserIcon } from 'lucide-react';

export const Layout: FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 bg-slate-900/80 border-b border-slate-800/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Brand Logo & Name */}
            <div className="flex items-center gap-8">
              <NavLink to="/" className="flex items-center gap-3 group">
                <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center transition-all group-hover:scale-105 group-hover:border-emerald-500/40 shadow-inner">
                  <Activity className="w-5 h-5" />
                </div>
                <div className="flex flex-col">
                  <span className="font-bold text-base tracking-tight text-white group-hover:text-emerald-400 transition-colors">
                    API Sentinel
                  </span>
                  <span className="text-[10px] text-slate-400 uppercase tracking-widest font-mono">
                    Live Health & Alerting
                  </span>
                </div>
              </NavLink>

              {/* Navigation Tabs */}
              <nav className="hidden sm:flex items-center gap-1">
                <NavLink
                  to="/"
                  end
                  className={({ isActive }) =>
                    `px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-slate-800 text-emerald-400 border border-slate-700/60 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`
                  }
                >
                  Dashboard
                </NavLink>

                <NavLink
                  to="/incidents"
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-slate-800 text-emerald-400 border border-slate-700/60 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`
                  }
                >
                  <Bell className="w-4 h-4" />
                  <span>Incidents</span>
                </NavLink>
              </nav>
            </div>

            {/* User Profile & Logout */}
            <div className="flex items-center gap-3">
              <div className="hidden md:flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800">
                <div className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                  <UserIcon className="w-4 h-4" />
                </div>
                <div className="flex flex-col text-left">
                  <span className="text-xs font-semibold text-slate-200">{user?.username}</span>
                  <span className="text-[10px] text-slate-400">{user?.email}</span>
                </div>
                {user?.is_superuser && (
                  <span className="ml-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    ADMIN
                  </span>
                )}
              </div>

              <button
                type="button"
                onClick={handleLogout}
                aria-label="Log out"
                title="Log out"
                className="flex items-center gap-2 px-3 py-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-all text-sm font-medium"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Subtle Footer */}
      <footer className="border-t border-slate-800/60 py-4 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>API Sentinel Uptime & Incident System</span>
          </div>
          <p>Protected by In-Memory JWT Authentication & Tenant Isolation</p>
        </div>
      </footer>
    </div>
  );
};

