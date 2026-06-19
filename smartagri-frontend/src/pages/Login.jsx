import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Leaf, Loader2 } from 'lucide-react';
import API from '../api/axios';

export default function Login() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const res = await API.post('/api/auth/login', formData);
      localStorage.setItem('smartagri_token', res.data.access_token);
      localStorage.setItem('smartagri_user', JSON.stringify(res.data.user));
      navigate('/voice-consultant');
    } catch (err) {
      const detail = err.response?.data?.detail;
      let errorMsg = 'Login failed. Please check your credentials.';
      if (detail) {
        if (Array.isArray(detail)) {
          errorMsg = detail.map(d => `${d.loc[d.loc.length - 1]}: ${d.msg}`).join('\n');
        } else if (typeof detail === 'string') {
          errorMsg = detail;
        } else {
          errorMsg = JSON.stringify(detail);
        }
      }
      alert(errorMsg);
      setIsLoading(false);
    }
  };

  return (
    <div className="app-frame flex flex-col justify-center min-h-[100dvh]">
      <div className="px-6 py-10 w-full animate-fade-in relative z-10">
        
        {/* Header */}
        <div className="text-center mb-12">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-[1.5rem] app-gradient shadow-xl mb-6">
            <Leaf className="text-white h-10 w-10" />
          </div>
          <h1 className="text-3xl font-black text-[var(--brand-950)] tracking-tight">SmartAgri</h1>
          <p className="text-xs text-gray-400 font-bold uppercase tracking-widest mt-1">Welcome Back Farmer</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="relative group">
            <label className="block text-xs font-bold uppercase tracking-wider text-[var(--text-500)] mb-1 px-1">Email Address</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="farmer@example.com"
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3.5 text-sm outline-none transition-all focus:border-[var(--brand-500)] focus:bg-white focus:ring-4 focus:ring-[var(--brand-100)]"
              required
            />
          </div>

          <div className="relative group">
            <label className="block text-xs font-bold uppercase tracking-wider text-[var(--text-500)] mb-1 px-1">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="••••••••"
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3.5 text-sm outline-none transition-all focus:border-[var(--brand-500)] focus:bg-white focus:ring-4 focus:ring-[var(--brand-100)]"
              required
            />
          </div>

          <button type="submit" disabled={isLoading} className="app-button flex items-center justify-center gap-2 mt-2">
            {isLoading ? <><Loader2 className="w-5 h-5 animate-spin" /> Authenticating...</> : 'Enter Dashboard'}
          </button>
        </form>

        <p className="text-center mt-8 text-sm text-[var(--text-500)] font-medium">
          New to SmartAgri? <Link to="/signup" className="text-[var(--brand-600)] font-bold hover:underline">Create an account</Link>
        </p>

      </div>
    </div>
  );
}
