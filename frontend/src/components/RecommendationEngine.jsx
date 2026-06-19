import React, { useState, useEffect } from 'react';
import { Sparkles, TrendingUp, Sun, CircleDollarSign, Sprout, Loader2, Award, Calendar } from 'lucide-react';
import API from '../api/axios';
import { useLanguage } from '../context/LanguageContext';

export default function RecommendationEngine() {
  const [reco, setReco] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expressing, setExpressing] = useState(false);
  const { t } = useLanguage();

  useEffect(() => {
    fetchReco();
  }, []);

  const fetchReco = async () => {
    try {
      const res = await API.get('/api/recommendations/crop');
      setReco(res.data.recommendation);
    } catch (err) {
      console.error("Failed to fetch crop recommendation:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleInterest = async () => {
    if (!reco) return;
    setExpressing(true);
    try {
      await API.post('/api/recommendations/interested', { crop_name: reco.crop_name });
      alert(`Interest registered! Expected vendor contact: ${reco.vendor_match?.name || 'Local Agronomist'}`);
      setReco(prev => ({ ...prev, interested: true }));
    } catch (err) {
      console.error(err);
      alert('Failed to register interest.');
    } finally {
      setExpressing(false);
    }
  };

  if (loading) return (
    <div className="app-card h-[400px] flex items-center justify-center">
      <div className="flex flex-col items-center gap-2">
        <Loader2 className="w-8 h-8 text-[var(--brand-500)] animate-spin" />
        <span className="text-xs text-gray-500 font-bold">{t('consultingKrishi')}</span>
      </div>
    </div>
  );

  if (!reco) return (
    <div className="app-card p-6 text-center text-xs text-gray-500 font-bold bg-white">
      {t('failedToGenerate')}
    </div>
  );

  return (
    <div className="flex flex-col gap-5 w-full animate-fade-in">

      {/* Reco Hero Banner */}
      <div className="bg-gradient-to-br from-purple-700 via-purple-600 to-indigo-800 text-white rounded-3xl p-5 shadow-xl relative overflow-hidden">
        <div className="absolute -top-4 -right-4 w-24 h-24 bg-white/10 rounded-full" />
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="w-5 h-5 text-purple-200 animate-pulse" />
          <span className="text-[10px] font-black uppercase tracking-widest text-purple-100">
            {t('topAlternativePick')}
          </span>
        </div>
        <h3 className="text-2xl font-black">{reco.crop_name}</h3>
        <p className="text-xs text-purple-100/90 leading-relaxed mt-2 font-medium">
          {reco.why_suitable}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4">
        <div className="app-card p-4 bg-white">
          <div className="flex items-center gap-1.5 text-purple-600 mb-1">
            <CircleDollarSign className="w-4 h-4" />
            <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">{t('estProfit')}</span>
          </div>
          <p className="text-lg font-black text-gray-900">
            ₹{reco.expected_profit_inr ? reco.expected_profit_inr.toLocaleString('en-IN') : 'N/A'}
          </p>
          <span className="text-[9px] text-gray-400 font-semibold">{t('perAcrePerSeason')}</span>
        </div>

        <div className="app-card p-4 bg-white">
          <div className="flex items-center gap-1.5 text-purple-600 mb-1">
            <Calendar className="w-4 h-4" />
            <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">{t('duration')}</span>
          </div>
          <p className="text-lg font-black text-gray-900">
            {reco.grow_duration_days || '180'} {t('days')}
          </p>
          <span className="text-[9px] text-gray-400 font-semibold">{t('fromSeedToHarvest')}</span>
        </div>
      </div>

      {/* Details Card */}
      <div className="app-card p-4 bg-white space-y-3">
        <div>
          <h4 className="text-[10px] font-black uppercase tracking-wider text-gray-400">{t('yieldExpectation')}</h4>
          <p className="text-sm font-bold text-gray-800 mt-0.5">{reco.expected_yield_per_acre || 'Flexible'}</p>
        </div>
        
        <div>
          <h4 className="text-[10px] font-black uppercase tracking-wider text-gray-400">{t('bestSowingSeason')}</h4>
          <p className="text-sm font-bold text-gray-800 mt-0.5">{reco.best_season || 'Any'}</p>
        </div>

        <div className="border-t border-gray-100 pt-3">
          <h4 className="text-[10px] font-black uppercase tracking-wider text-gray-400">{t('specialCareTips')}</h4>
          <p className="text-xs text-gray-600 leading-relaxed font-medium mt-1">{reco.care_tips}</p>
        </div>
      </div>

      {/* Matched Buyer Info */}
      {reco.vendor_match ? (
        <div className="app-card p-4 bg-blue-50/50 border border-blue-100 rounded-3xl">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">🤝</span>
            <span className="text-[10px] font-black text-blue-700 uppercase tracking-widest">{t('matchedBuyerGuaranteed')}</span>
          </div>
          <h4 className="font-black text-blue-900 text-sm">{reco.vendor_match.name}</h4>
          <p className="text-xs text-blue-700 mt-0.5 font-medium">{reco.vendor_match.location}</p>
        </div>
      ) : (
        <div className="app-card p-4 bg-gray-50 border border-gray-100 rounded-3xl">
          <p className="text-xs text-gray-500 font-medium">
            💡 {t('localAgronomistsDesc')}
          </p>
        </div>
      )}

      {/* Interest Button */}
      <button 
        onClick={handleInterest}
        disabled={expressing || reco.interested}
        className={`w-full py-4 rounded-2xl font-black text-sm transition-all flex items-center justify-center gap-2 shadow-lg disabled:opacity-70 disabled:cursor-not-allowed
           ${reco.interested 
             ? 'bg-gray-100 text-gray-400 border border-gray-200' 
             : 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-700 hover:to-indigo-700'}`}
      >
        {expressing ? (
          <Loader2 className="w-5 h-5 animate-spin"/>
        ) : reco.interested ? (
          t('interestRegistered')
        ) : (
          <>
            <Sprout className="w-5 h-5"/> 
            {t('adoptCropThisSeason')}
          </>
        )}
      </button>

      <div className="h-6" />
    </div>
  );
}
