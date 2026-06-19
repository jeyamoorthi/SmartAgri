import React from 'react';
import { User, MapPin, Droplets, Thermometer, Database } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function FarmerAvatar({ user }) {
  const { t } = useLanguage();
  if (!user) return null;

  const weather = user.weather_data || {};
  const soil = user.soil_data || {};

  return (
    <div className="bg-white rounded-3xl border border-[var(--line)] shadow-sm overflow-hidden animate-fade-in relative">
      <div className="p-4 flex items-center gap-4">
        {/* Avatar Circle */}
        <div className="w-14 h-14 rounded-2xl bg-[var(--brand-50)] border border-[var(--brand-200)] flex items-center justify-center text-[var(--brand-700)] flex-shrink-0">
          <User className="w-8 h-8" />
        </div>

        {/* Farmer Info */}
        <div className="flex-1 min-w-0">
          <h2 className="text-base font-black text-[var(--text-900)] truncate">
            {user.username || user.full_name || 'Farmer'}
          </h2>
          <div className="flex items-center gap-1 text-xs text-gray-500 font-semibold mt-0.5">
            <MapPin className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
            <span className="truncate">{user.location || 'Tamil Nadu, India'}</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-[var(--brand-700)] font-bold mt-1">
            <span className="bg-[var(--brand-50)] border border-[var(--brand-100)] px-2 py-0.5 rounded-lg">
              {user.land_acres || 2} {t('acres')}
            </span>
            <span className="bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-lg text-emerald-700">
              {user.present_crop || 'Paddy'} ({user.present_crop_stage || 'Vegetative'})
            </span>
          </div>
        </div>
      </div>

      {/* Soil & Weather Stats Grid */}
      <div className="grid grid-cols-3 divide-x divide-gray-100 bg-gray-50/50 border-t border-[var(--line)] py-3 px-2">
        <div className="text-center">
          <div className="flex items-center justify-center gap-1 text-gray-400 mb-0.5">
            <Thermometer className="w-3.5 h-3.5" />
            <span className="text-[10px] font-bold uppercase tracking-wider">{t('temp')}</span>
          </div>
          <p className="text-xs font-bold text-[var(--text-900)]">{weather.temp || '32'}°C</p>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center gap-1 text-gray-400 mb-0.5">
            <Droplets className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-[10px] font-bold uppercase tracking-wider">{t('soilPH')}</span>
          </div>
          <p className="text-xs font-bold text-[var(--text-900)]">{soil.ph || '6.8'}</p>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center gap-1 text-gray-400 mb-0.5">
            <Database className="w-3.5 h-3.5 text-amber-500" />
            <span className="text-[10px] font-bold uppercase tracking-wider">N-P-K</span>
          </div>
          <p className="text-[10px] font-bold text-[var(--text-900)] truncate px-1">
            {soil.nitrogen_kg_ha || 120} : {soil.phosphorus_kg_ha || 35} : {soil.potassium_kg_ha || 80}
          </p>
        </div>
      </div>
    </div>
  );
}
