import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, Store, PackageSearch, Loader2, IndianRupee, MapPin } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import API from '../api/axios';
import { useLanguage } from '../context/LanguageContext';

export default function MarketTrends() {
  const [data, setData] = useState(null);
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const { t } = useLanguage();

  useEffect(() => {
    fetchMarketData();
  }, []);

  const fetchMarketData = async () => {
    try {
      const [trendRes, vendorRes] = await Promise.all([
        API.get('/api/market/trends'),
        API.get('/api/market/vendors')
      ]);
      setData(trendRes.data);
      setVendors(vendorRes.data.vendors || []);
    } catch (err) {
      console.error("Failed to fetch market data:", err);
    } finally {
      setLoading(false);
    }
  };

  const getTrendIcon = (dir) => {
    if (dir === 'rising') return <TrendingUp className="w-5 h-5 text-emerald-500" />;
    if (dir === 'falling') return <TrendingDown className="w-5 h-5 text-red-500" />;
    return <Minus className="w-5 h-5 text-gray-500" />;
  };

  if (loading) return (
    <div className="app-card h-[400px] flex items-center justify-center">
      <div className="flex flex-col items-center gap-2">
        <Loader2 className="w-8 h-8 text-[var(--brand-500)] animate-spin" />
        <span className="text-xs text-gray-500 font-bold">{t('analyzingMarketData')}</span>
      </div>
    </div>
  );

  if (!data) return null;

  // Format chart data for recharts
  const chartData = (data.trends || []).map((t, idx) => {
    const ts = t.timestamp ? new Date(t.timestamp) : new Date();
    return {
      name: ts.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }),
      price: t.price_per_quintal || 0,
      crop: t.crop_name || data.crop
    };
  });

  return (
    <div className="flex flex-col gap-6 w-full animate-fade-in">
      
      {/* Overview Stat Cards */}
      <div className="grid grid-cols-2 gap-4">
        <div className="app-card p-4 bg-white relative overflow-hidden">
          <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{t('cropSegment')}</div>
          <div className="text-lg font-black text-emerald-950 capitalize mt-1">{data.crop}</div>
          <div className="absolute top-4 right-4 bg-emerald-50 text-emerald-700 p-1.5 rounded-lg">
            <Store className="w-4 h-4" />
          </div>
        </div>

        <div className="app-card p-4 bg-white relative overflow-hidden">
          <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{t('avgPrice')}</div>
          <div className="text-lg font-black text-emerald-950 mt-1 flex items-center">
            <IndianRupee className="w-4.5 h-4.5 text-gray-500" />
            <span>{data.average_price}/qtl</span>
          </div>
          <div className="absolute top-4 right-4 bg-gray-50 p-1.5 rounded-lg">
            {getTrendIcon(data.trend_direction)}
          </div>
        </div>
      </div>

      {/* Chart Section */}
      <div className="app-card p-4 bg-white">
        <div className="flex items-center justify-between mb-4 border-b border-gray-100 pb-3">
          <div>
            <h3 className="font-black text-sm text-gray-900">{t('mandiPriceMovement')}</h3>
            <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider mt-0.5">{t('last30Days')}</p>
          </div>
          <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-800 text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full">
            {t(data.trend_direction + 'Trend')}
          </div>
        </div>

        <div className="h-[220px] w-full">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 5, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#37a372" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#37a372" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" tick={{ fontSize: 9, fontWeight: 'bold' }} stroke="#9ca3af" />
                <YAxis tick={{ fontSize: 9, fontWeight: 'bold' }} stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(255, 255, 255, 0.95)',
                    border: '1px solid #e5e7eb',
                    borderRadius: '12px',
                    boxShadow: '0 10px 15px -3px rgba(0,0,0,0.05)',
                  }}
                  labelStyle={{ color: '#6b7280', fontSize: '11px', fontWeight: 'bold' }}
                  itemStyle={{ color: '#111827', fontSize: '12px', fontWeight: 'bold' }}
                />
                <Area type="monotone" dataKey="price" stroke="#37a372" strokeWidth={3} fillOpacity={1} fill="url(#colorPrice)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-gray-400 font-bold">
              {t('noPriceTrends')}
            </div>
          )}
        </div>
      </div>

      {/* Verified Local Buyers */}
      <div className="app-card flex flex-col overflow-hidden max-h-[300px]">
        <div className="p-3 border-b border-gray-100 bg-gray-50 flex items-center gap-2">
          <Store className="w-4 h-4 text-[var(--brand-600)]" />
          <h3 className="font-black text-sm text-gray-900">{t('verifiedMandiBuyers')}</h3>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-2.5 bg-white">
          {vendors.filter(v => v.match).map(v => (
            <div key={v.id} className="p-3 bg-white border border-gray-200 rounded-2xl hover:border-[var(--brand-300)] transition-all flex justify-between items-center group">
              <div className="min-w-0">
                <h4 className="font-black text-gray-900 text-sm group-hover:text-[var(--brand-700)] transition-colors truncate">
                  {v.name}
                </h4>
                <div className="flex items-center gap-1 mt-1 text-[11px] text-gray-500 font-semibold">
                  <MapPin className="w-3.5 h-3.5 text-gray-400" />
                  <span className="truncate">{v.location}</span>
                </div>
              </div>
              <a 
                href={`tel:${v.contact}`}
                className="bg-[var(--brand-50)] text-[var(--brand-700)] hover:bg-[var(--brand-100)] p-2.5 rounded-xl transition-colors flex-shrink-0"
              >
                <PackageSearch className="w-4.5 h-4.5" />
              </a>
            </div>
          ))}
          {vendors.filter(v => v.match).length === 0 && (
            <div className="text-center text-xs text-gray-400 py-6 font-bold">
              {t('noDirectBuyers')} "{data.crop}".
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
