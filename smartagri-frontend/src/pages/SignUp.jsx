import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Leaf, MapPin, Loader2 } from 'lucide-react';
import API from '../api/axios';

export default function SignUp() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    location: '',
    present_crop: 'paddy',
    present_crop_stage: 'vegetative',
    land_acres: 2,
    gps_coordinates: { lat: 13.0827, lng: 80.2707 } // default Chennai coordinates
  });

  useEffect(() => {
    // Detect geolocation
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setFormData((prev) => ({
            ...prev,
            gps_coordinates: {
              lat: position.coords.latitude,
              lng: position.coords.longitude
            }
          }));
        },
        (error) => {
          console.log("Geolocation detection failed, using defaults:", error);
        }
      );
    }
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'land_acres' ? parseFloat(value) || 0 : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await API.post('/api/auth/register', formData);
      alert('Registration successful! Please login.');
      navigate('/login');
    } catch (err) {
      console.error(err);
      const detail = err.response?.data?.detail;
      let errorMsg = 'Registration failed';
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
    <div className="app-frame flex flex-col justify-center min-h-[100dvh] py-8">
      <div className="px-6 w-full animate-fade-in relative z-10">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[1.25rem] app-gradient shadow-lg mb-4">
            <Leaf className="text-white h-8 w-8" />
          </div>
          <h1 className="text-2xl font-black text-[var(--brand-950)] tracking-tight">SmartAgri Register</h1>
          <p className="text-xs text-gray-400 font-bold uppercase tracking-widest mt-1">Start natural precision farming</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">Farmer Name</label>
              <input
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                placeholder="e.g. Ramesh Kumar"
                className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-xs font-semibold outline-none focus:border-[var(--brand-500)] focus:bg-white"
                required
              />
            </div>
            <div>
              <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">Username</label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="e.g. ramesh"
                className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-xs font-semibold outline-none focus:border-[var(--brand-500)] focus:bg-white"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">Email Address</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="farmer@example.com"
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-xs font-semibold outline-none focus:border-[var(--brand-500)] focus:bg-white"
              required
            />
          </div>

          <div>
            <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="••••••••"
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-xs font-semibold outline-none focus:border-[var(--brand-500)] focus:bg-white"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">District / Location</label>
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                placeholder="e.g. Madurai, TN"
                className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-xs font-semibold outline-none focus:border-[var(--brand-500)] focus:bg-white"
                required
              />
            </div>
            <div>
              <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">Land (Acres)</label>
              <input
                type="number"
                name="land_acres"
                value={formData.land_acres}
                onChange={handleChange}
                placeholder="2"
                min="0.1"
                step="0.1"
                className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-xs font-semibold outline-none focus:border-[var(--brand-500)] focus:bg-white"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">Current Crop</label>
              <select
                name="present_crop"
                value={formData.present_crop}
                onChange={handleChange}
                className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-xs font-semibold outline-none focus:border-[var(--brand-500)] focus:bg-white appearance-none"
              >
                <option value="paddy">Paddy / Rice</option>
                <option value="tomato">Tomato</option>
                <option value="potato">Potato</option>
                <option value="onion">Onion</option>
                <option value="cotton">Cotton</option>
              </select>
            </div>
            <div>
              <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">Crop Stage</label>
              <select
                name="present_crop_stage"
                value={formData.present_crop_stage}
                onChange={handleChange}
                className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-xs font-semibold outline-none focus:border-[var(--brand-500)] focus:bg-white appearance-none"
              >
                <option value="sowing">Sowing / Planting</option>
                <option value="vegetative">Vegetative Growth</option>
                <option value="flowering">Flowering</option>
                <option value="harvest">Near Harvest</option>
              </select>
            </div>
          </div>

          {/* GPS Detector display */}
          <div className="bg-gray-50 border border-gray-100 rounded-2xl p-3 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-red-500 flex-shrink-0" />
            <div className="min-w-0">
              <span className="block text-[9px] font-black text-gray-400 uppercase tracking-widest">GPS Coordinates Detected</span>
              <span className="text-xs text-gray-700 font-mono font-bold">
                {formData.gps_coordinates.lat.toFixed(4)}° N, {formData.gps_coordinates.lng.toFixed(4)}° E
              </span>
            </div>
          </div>

          <button type="submit" disabled={isLoading} className="app-button flex items-center justify-center gap-2 mt-2">
            {isLoading ? <><Loader2 className="w-5 h-5 animate-spin" /> Creating Profile...</> : 'Complete Profile & Join'}
          </button>
        </form>

        <p className="text-center mt-6 text-sm text-[var(--text-500)] font-medium">
          Already have an account? <Link to="/login" className="text-[var(--brand-600)] font-bold hover:underline">Log in</Link>
        </p>

      </div>
    </div>
  );
}
