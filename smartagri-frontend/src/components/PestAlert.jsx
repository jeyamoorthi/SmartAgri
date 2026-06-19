import React, { useState, useEffect } from 'react';
import { Bug, AlertTriangle, Send, Loader2, Info, MapPin } from 'lucide-react';
import API from '../api/axios';
import { useLanguage } from '../context/LanguageContext';

export default function PestAlert() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reporting, setReporting] = useState(false);
  const { t } = useLanguage();
  const [reportData, setReportData] = useState({
    pest_name: '',
    severity: 5,
  });

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const res = await API.get('/api/pest/alerts');
      setAlerts(res.data.alerts || []);
    } catch (err) {
      console.error("Failed to fetch pest alerts:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleReport = async (e) => {
    e.preventDefault();
    if (!reportData.pest_name) return;
    
    setReporting(true);
    try {
      const res = await API.post('/api/pest/report', reportData);
      alert(`Pest sighting broadcasted! Notified ${res.data.nearby_farmers_notified} nearby farmers.`);
      setReportData({ pest_name: '', severity: 5 });
      fetchAlerts();
    } catch (err) {
      console.error(err);
      alert('Failed to report sighting.');
    } finally {
      setReporting(false);
    }
  };

  if (loading) return (
    <div className="app-card h-[300px] flex items-center justify-center">
      <div className="flex flex-col items-center gap-2">
        <Loader2 className="w-8 h-8 text-[var(--brand-500)] animate-spin" />
        <span className="text-xs text-gray-500 font-bold">{t('scanningDatabases')}</span>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col gap-5 w-full animate-fade-in">
      
      {/* Active Alerts List */}
      <div className="app-card flex flex-col overflow-hidden max-h-[350px]">
        <div className="p-3 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <h3 className="font-black text-sm text-gray-900">{t('activeThreats')}</h3>
          </div>
          <span className="text-[10px] bg-red-100 text-red-700 font-bold px-2 py-0.5 rounded-full">
            {alerts.length} {t('active')}
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-2.5 bg-white">
          {alerts.map((alertItem, idx) => {
            const timeStr = alertItem.reported_at ? new Date(alertItem.reported_at).toLocaleDateString('en-IN', { hour: '2-digit', minute: '2-digit' }) : 'Recently';
            return (
              <div key={idx} className="p-3 bg-red-50/40 border border-red-100 rounded-2xl flex items-start gap-3">
                <div className="bg-red-100 text-red-700 p-2 rounded-xl mt-0.5 flex-shrink-0">
                  <Bug className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h4 className="font-black text-gray-900 text-sm truncate">{alertItem.pest_name}</h4>
                    <span className="text-[10px] bg-red-500 text-white font-bold px-1.5 py-0.5 rounded">
                      Sev: {alertItem.severity}/10
                    </span>
                  </div>
                  <div className="flex items-center gap-1 mt-1 text-[10px] text-gray-500 font-semibold">
                    <MapPin className="w-3 h-3 text-red-400" />
                    <span className="truncate">{alertItem.location || 'Cluster area'}</span>
                    <span className="mx-1">·</span>
                    <span>{timeStr}</span>
                  </div>
                </div>
              </div>
            );
          })}
          {alerts.length === 0 && (
            <div className="text-center text-xs text-gray-400 py-10 font-bold flex flex-col items-center gap-2">
              <Info className="w-8 h-8 text-emerald-500" />
              <span>{t('allClearPest')}</span>
            </div>
          )}
        </div>
      </div>

      {/* Report Form */}
      <div className="app-card p-4 bg-white">
        <h4 className="font-black text-[var(--text-900)] text-sm mb-3 flex items-center gap-2">
          <Bug className="w-4 h-4 text-red-500" /> 
          {t('reportPestSighting')}
        </h4>
        <form onSubmit={handleReport} className="space-y-4">
          <div>
            <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">{t('pestDiseaseName')}</label>
            <input
              type="text"
              placeholder="e.g. Tomato Late Blight, Stem Borer"
              className="w-full text-sm p-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:border-red-400 focus:bg-white transition-all font-semibold"
              value={reportData.pest_name}
              onChange={e => setReportData({...reportData, pest_name: e.target.value})}
              required
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1 px-1">
              <label className="text-[10px] font-black uppercase tracking-wider text-gray-400">{t('severityLevel')}</label>
              <span className="text-xs font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded-lg border border-red-100">
                {reportData.severity} / 10
              </span>
            </div>
            <input 
              type="range" 
              min="1" 
              max="10" 
              value={reportData.severity}
              onChange={e => setReportData({...reportData, severity: parseInt(e.target.value)})}
              className="w-full cursor-pointer accent-red-500"
            />
          </div>

          <button 
            type="submit" 
            disabled={reporting}
            className="w-full bg-red-50 hover:bg-red-100 text-red-700 font-bold text-sm py-3.5 rounded-xl border border-red-200 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {reporting ? (
              <Loader2 className="w-4 h-4 animate-spin"/>
            ) : (
              <>
                <Send className="w-4 h-4"/> 
                {t('broadcastSighting')}
              </>
            )}
          </button>
        </form>
      </div>

    </div>
  );
}
