import React, { useEffect, useState } from 'react';
import { Outlet, useNavigate, NavLink } from 'react-router-dom';
import { LogOut, Home, TrendingUp, ShieldAlert, Award, Mic, Camera } from 'lucide-react';
import API from '../api/axios';
import VoiceAssistantFAB from './VoiceAssistantFAB';
import { useLanguage } from '../context/LanguageContext';

const LANGUAGES_LIST = [
  { code: 'en', native: 'English' },
  { code: 'hi', native: 'हिन्दी' },
  { code: 'ta', native: 'தமிழ்' },
  { code: 'te', native: 'తెలుగు' },
  { code: 'kn', native: 'ಕನ್ನಡ' },
  { code: 'ml', native: 'മലയാളം' },
  { code: 'bn', native: 'বাংলা' },
  { code: 'gu', native: 'ગુજરાતી' },
  { code: 'mr', native: 'मराठी' },
  { code: 'pa', native: 'ਪੰਜਾਬੀ' },
  { code: 'or', native: 'ଓଡ଼ିଆ' },
  { code: 'as', native: 'অসমীয়া' },
  { code: 'ur', native: 'اردو' }
];

export default function DashboardLayout() {
  const navigate = useNavigate();
  const { language, changeLanguage, t } = useLanguage();
  const [errorStatus, setErrorStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await API.get('/api/auth/me');
        localStorage.setItem('smartagri_user', JSON.stringify(res.data));
        setLoading(false);
      } catch (err) {
        if (err.response && err.response.status === 401) {
          // Token expired — redirect to login
          localStorage.removeItem('smartagri_token');
          localStorage.removeItem('smartagri_user');
          navigate('/login');
        } else {
          setErrorStatus('Cannot connect to the SmartAgri backend. Please ensure the API server is running on port 8001.');
          setLoading(false);
        }
      }
    };
    fetchUser();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('smartagri_token');
    localStorage.removeItem('smartagri_user');
    navigate('/login');
  };

  if (errorStatus) {
    return (
      <div className="min-h-screen bg-[var(--off-white)] flex flex-col items-center justify-center p-6 text-center">
        <div className="text-5xl mb-4">🌾</div>
        <h2 className="text-xl font-bold text-red-600 mb-2">Connection Error</h2>
        <p className="text-gray-600 mb-4 max-w-sm">{errorStatus}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-2 bg-[var(--brand-600)] text-white rounded-xl shadow-md font-medium hover:bg-[var(--brand-700)] transition-colors"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--off-white)] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="text-4xl animate-bounce">🌱</div>
          <div className="animate-pulse text-[var(--brand-600)] font-semibold text-sm">
            Loading your digital farm...
          </div>
        </div>
      </div>
    );
  }

  const navItemsLeft = [
    { path: '/home', label: t('home'), icon: Home },
    { path: '/market', label: t('market'), icon: TrendingUp },
  ];

  const navItemsRight = [
    { path: '/disease', label: t('diseaseScan'), icon: Camera },
    { path: '/recommendations', label: t('crops'), icon: Award },
  ];

  return (
    <div className="min-h-screen bg-[var(--off-white)] flex flex-col max-w-[480px] mx-auto shadow-2xl relative overflow-x-hidden">

      {/* ── Top Header Bar ── */}
      <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-xl border-b border-[var(--line)] px-3 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <span className="text-xl">🌾</span>
          <div>
            <span className="text-xs font-black text-[var(--brand-700)] tracking-tight">SmartAgri</span>
            <div className="text-[8px] text-gray-400 font-semibold uppercase tracking-wider -mt-0.5">Precision</div>
          </div>
        </div>

        {/* Global Language Selector */}
        <div className="flex items-center gap-1 bg-emerald-50 border border-emerald-100 rounded-xl px-2 py-1 flex-shrink-0">
          <span className="text-[8px] font-black text-emerald-800 tracking-wider">LANG</span>
          <select 
            value={language} 
            onChange={(e) => changeLanguage(e.target.value)}
            className="bg-transparent text-[11px] font-black text-emerald-950 outline-none cursor-pointer"
          >
            {LANGUAGES_LIST.map(lang => (
              <option key={lang.code} value={lang.code}>
                {lang.native}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handleLogout}
          className="flex items-center gap-1 text-[11px] font-bold text-gray-500 hover:text-red-500 transition-colors px-2 py-1 rounded-lg hover:bg-red-50 flex-shrink-0"
        >
          <LogOut className="w-3.5 h-3.5" />
          {t('logout')}
        </button>
      </header>

      {/* ── Page Content ── */}
      <main className="flex-1 overflow-y-auto pb-24">
        <Outlet />
      </main>

      {/* ── Bottom Navigation ── */}
      <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[480px] z-40 bg-white/95 backdrop-blur-xl border-t border-[var(--line)] px-1 py-1.5 flex items-center justify-between shadow-lg safe-bottom">
        
        {/* Left items */}
        <div className="flex items-center justify-around flex-1">
          {navItemsLeft.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl transition-all duration-200 text-[10px] font-bold ${
                  isActive
                    ? 'text-[var(--brand-700)] bg-[var(--brand-50)]'
                    : 'text-gray-400 hover:text-gray-600'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              <span className="truncate max-w-[70px]">{label}</span>
            </NavLink>
          ))}
        </div>

        {/* Center Spacer */}
        <div className="w-16 h-12 flex-shrink-0 flex items-center justify-center relative" />

        {/* Right items */}
        <div className="flex items-center justify-around flex-1">
          {navItemsRight.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl transition-all duration-200 text-[10px] font-bold ${
                  isActive
                    ? 'text-[var(--brand-700)] bg-[var(--brand-50)]'
                    : 'text-gray-400 hover:text-gray-600'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              <span className="truncate max-w-[70px]">{label}</span>
            </NavLink>
          ))}
        </div>

      </nav>

      {/* ── Floating Voice Assistant FAB ── */}
      <VoiceAssistantFAB />
    </div>
  );
}