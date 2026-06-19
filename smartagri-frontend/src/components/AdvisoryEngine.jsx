import React, { useState, useEffect } from 'react';
import { Calendar, Droplet, Sprout, Wheat, Loader2, RefreshCw } from 'lucide-react';
import API from '../api/axios';
import { useLanguage } from '../context/LanguageContext';

export default function AdvisoryEngine() {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const { t } = useLanguage();

  useEffect(() => {
    fetchPlan();
  }, []);

  const fetchPlan = async () => {
    try {
      const res = await API.get('/api/advisory/current-plan');
      if (res.data.status === 'success') {
        setPlan(res.data.plan);
      }
    } catch (err) {
      console.error("Failed to fetch advisory plan:", err);
    } finally {
      setLoading(false);
    }
  };

  const generatePlan = async () => {
    setGenerating(true);
    try {
      const res = await API.post('/api/advisory/generate-plan', {});
      if (res.data.status === 'success') {
        setPlan(res.data.plan);
      }
    } catch (err) {
      console.error("Failed to generate plan:", err);
      alert('Failed to generate advisory plan.');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) return (
    <div className="app-card h-[250px] flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-[var(--brand-500)] animate-spin" />
    </div>
  );

  return (
    <div className="flex flex-col gap-4 w-full animate-fade-in">
      {!plan ? (
        <div className="app-card p-6 text-center space-y-4 bg-white">
          <div className="text-4xl">🗓️</div>
          <div>
            <h3 className="font-black text-sm text-gray-900">{t('noWeeklyAdvisory')}</h3>
            <p className="text-xs text-gray-400 mt-1">{t('customizedSchedulesDesc')}</p>
          </div>
          <button
            onClick={generatePlan}
            disabled={generating}
            className="w-full bg-[var(--brand-700)] text-white font-bold py-3 rounded-xl hover:bg-[var(--brand-800)] transition-all flex items-center justify-center gap-2 shadow-lg disabled:opacity-50"
          >
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : t('generateWeeklyPlan')}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Irrigation Schedule */}
          <div className="app-card p-4 bg-white">
            <h4 className="font-black text-xs text-[var(--brand-700)] uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Droplet className="w-4 h-4 text-blue-500" />
              {t('irrigationSchedule')}
            </h4>
            <div className="divide-y divide-gray-100">
              {(plan.irrigation_schedule || []).map((slot, idx) => (
                <div key={idx} className="py-2.5 flex justify-between items-center text-xs font-semibold">
                  <span className="text-gray-900">{slot.day} · {slot.time}</span>
                  <span className="text-gray-500 bg-blue-50 border border-blue-100 px-2 py-0.5 rounded-lg">
                    {slot.duration_mins} mins ({slot.method || 'Drip'})
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Pest Warnings */}
          <div className="app-card p-4 bg-white">
            <h4 className="font-black text-xs text-[var(--brand-700)] uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Sprout className="w-4 h-4 text-amber-500" />
              {t('pestWarnings')}
            </h4>
            <div className="space-y-2">
              {(plan.pest_warnings || []).map((p, idx) => (
                <div key={idx} className="text-xs bg-amber-50/50 border border-amber-100 p-2.5 rounded-xl">
                  <div className="flex justify-between font-bold text-gray-900 mb-0.5">
                    <span>{p.pest_name}</span>
                    <span className="text-amber-700 uppercase tracking-widest text-[9px]">{p.risk_level} Risk</span>
                  </div>
                  <p className="text-gray-600 font-medium">{p.remedy}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Harvest Plan */}
          {plan.harvest_plan && (
            <div className="app-card p-4 bg-white space-y-2">
              <h4 className="font-black text-xs text-[var(--brand-700)] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Wheat className="w-4 h-4 text-purple-500" />
                {t('harvestOutlook')}
              </h4>
              <div className="grid grid-cols-2 gap-2 text-xs font-semibold">
                <div className="bg-gray-50 p-2 rounded-xl border border-gray-100">
                  <span className="text-gray-400 block text-[9px] uppercase tracking-wider font-bold">{t('estDate')}</span>
                  <span className="text-gray-800">{plan.harvest_plan.expected_date || 'Flexible'}</span>
                </div>
                <div className="bg-gray-50 p-2 rounded-xl border border-gray-100">
                  <span className="text-gray-400 block text-[9px] uppercase tracking-wider font-bold">{t('yieldProjection')}</span>
                  <span className="text-gray-800">{plan.harvest_plan.yield_estimate || 'Average'}</span>
                </div>
              </div>
            </div>
          )}

          {/* Regeneration action */}
          <button
            onClick={generatePlan}
            disabled={generating}
            className="w-full border border-gray-200 text-gray-500 bg-white font-bold py-2.5 rounded-xl hover:bg-gray-50 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${generating ? 'animate-spin' : ''}`} />
            {t('regeneratePlan')}
          </button>
        </div>
      )}
    </div>
  );
}
