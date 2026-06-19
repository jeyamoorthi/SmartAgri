import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, ShieldAlert, Award, Mic, CloudSun, Leaf, ChevronRight, Camera } from 'lucide-react';
import FarmerAvatar from '../components/FarmerAvatar';
import { useLanguage, VOICE_SUGGESTIONS } from '../context/LanguageContext';

const FARM_TIPS = {
  en: "Apply Jivamrita once weekly to boost soil microbiome and reduce dependence on chemical inputs.",
  hi: "मिट्टी के सूक्ष्मजीवों को बढ़ाने और रासायनिक खादों पर निर्भरता कम करने के लिए सप्ताह में एक बार जीवामृत का प्रयोग करें।",
  ta: "மண் நுண்ணுயிரிகளை அதிகரிக்கவும், ரசாயன உள்ளீடுகளைக் குறைக்கவும் வாரத்திற்கு ஒருமுறை ஜீவாமிர்தம் தெளிக்கவும்.",
  te: "నేల సూక్ష్మజీవులను పెంచడానికి మరియు రసాయన ఎరువులపై ఆధారపడటాన్ని తగ్గించడానికి వారానికి ఒకసారి జీవామృతాన్ని ఉపయోగించండి.",
  kn: "ಮಣ್ಣಿನ ಸೂಕ್ಷ್ಮಜೀವಿಗಳನ್ನು ಹೆಚ್ಚಿಸಲು ಮತ್ತು ರಾಸಾಯನಿಕ ಗೊಬ್ಬರಗಳ ಮೇಲಿನ ಅವಲಂಬನೆಯನ್ನು ಕಡಿಮೆ ಮಾಡಲು ವಾರಕ್ಕೊಮ್ಮೆ ಜೀವಾಮೃತ ಬಳಸಿ.",
  ml: "മണ്ണിലെ സൂക്ഷ്മാണുക്കളെ വർദ്ധിപ്പിക്കുന്നതിനും രാസവളങ്ങളെ ആശ്രയിക്കുന്നത് കുറയ്ക്കുന്നതിനും ആഴ്ചയിലൊരിക്കൽ ജീവാമൃതം ഉപയോഗിക്കുക.",
  mr: "मातीतील सूक्ष्मजीव वाढवण्यासाठी आणि रासायनिक खतांवर अवलंबित्व कमी करण्यासाठी आठवड्यातून एकदा जीवामृत वापरा.",
  gu: "જમીનના સૂક્ષ્มજીવોને વધારવા અને રાસાયણિક ખાતરો પર નિર્ભરતા ઘટાડવા માટે અઠવાડિયામાં એકવાર જીવામૃતનો ઉપયોગ કરો.",
  pa: "ਮਿੱਟੀ ਦੇ ਸੂਖਮ ਜੀਵਾਂ ਨੂੰ ਵਧਾਉਣ ਅਤੇ ਰਸਾਇਣਕ ਖਾਦਾਂ 'ਤੇ ਨਿਰਭਰਤਾ ਘਟਾਉਣ ਲਈ ਹਫ਼ਤੇ ਵਿੱਚ ਇੱਕ ਵਾਰ ਜੀਵਾਮ੍ਰਿਤ ਦੀ ਵਰਤੋਂ ਕਰੋ।",
  bn: "মাটির অণুজীব বৃদ্ধি করতে এবং রাসায়নিক সারের উপর নির্ভরতা কমাতে সপ্তাহে একবার জীবামৃত ব্যবহার করুন।",
  or: "ମାଟିର ଅଣୁଜୀବ ବୃଦ୍ਧି କରିବା ଏବଂ ରାସାୟନିକ ସାର ଉପରେ ନିର୍ଭરଶୀଳତା ହ୍ରաս କରିବାକୁ ସପ୍ତାହରେ ଥରେ ଜੀବାମୃତ ପ୍ରୟୋਗ କରନ୍ତୁ ।",
  as: "মাটিৰ অণুজীৱ বৃদ্ধি কৰিবলৈ আৰু ৰাসায়নিক সাৰৰ ব্যৱহাৰ কমাবলৈ সপ্তাহত এবাৰ জীৱামৃত ব্যৱহাৰ কৰক।",
  ur: "مٹی کے خرد بینی جانداروں کو بڑھانے اور کیمیائی کھادوں پر انحصار کم کرنے کے لیے ہفتے میں ایک بار جیوا मृत کا استعمال کریں۔"
};

const GREETINGS = {
  en: { morning: "Good Morning", afternoon: "Good Afternoon", evening: "Good Evening" },
  hi: { morning: "सुप्रभात", afternoon: "नमस्कार", evening: "नमस्कार" },
  ta: { morning: "காலை வணக்கம்", afternoon: "மதிய வணக்கம்", evening: "மாலை வணக்கம்" },
  te: { morning: "శుభోదయం", afternoon: "నమస్కారం", evening: "నమస్కారం" },
  kn: { morning: "ಶುಭೋದಯ", afternoon: "ನಮಸ್ಕಾರ", evening: "ನಮಸ್ಕಾರ" },
  ml: { morning: "സുപ്രഭാതം", afternoon: "നമസ്കാരം", evening: "നമസ്കാരം" },
  mr: { morning: "शुभप्रभात", afternoon: "नमस्कार", evening: "नमस्कार" },
  gu: { morning: "સુપ્રભાત", afternoon: "નમસ્તે", evening: "નમસ્તે" },
  pa: { morning: "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ", afternoon: "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ", evening: "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ" },
  bn: { morning: "সুপ্রভাত", afternoon: "নমস্কার", evening: "নমস্কার" },
  or: { morning: "ଶୁଭ ସକାଳ", afternoon: "ନମସ୍କାର", evening: "ନମସ୍କାର" },
  as: { morning: "সুপ্রভাত", afternoon: "নমস্কাৰ", evening: "নমস্কাৰ" },
  ur: { morning: "صبح بخیر", afternoon: "اسلام علیکم", evening: "اسلام علیکم" }
};

export default function Home() {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [user, setUser] = useState(null);
  const [timeGreeting, setTimeGreeting] = useState('morning');

  useEffect(() => {
    const storedUser = localStorage.getItem('smartagri_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    const hr = new Date().getHours();
    if (hr < 12) setTimeGreeting('morning');
    else if (hr < 17) setTimeGreeting('afternoon');
    else setTimeGreeting('evening');
  }, []);

  if (!user) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-pulse text-[var(--brand-600)] font-semibold">
          Loading dashboard...
        </div>
      </div>
    );
  }

  const localizedGreeting = GREETINGS[language]?.[timeGreeting] || GREETINGS['en'][timeGreeting];
  const suggestions = VOICE_SUGGESTIONS[language] || VOICE_SUGGESTIONS['en'];
  const tipText = FARM_TIPS[language] || FARM_TIPS['en'];

  const quickLinks = [
    {
      name: t('mandiPrices'),
      desc: t('marketSnapshot'),
      path: '/market',
      icon: TrendingUp,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
      voice: language === 'ta' ? '"மண்டி விலை"' : language === 'hi' ? '"मंडी भाव"' : '"go to market"',
    },
    {
      name: t('diseaseScan'),
      desc: t('tapToAsk'),
      path: '/disease',
      icon: Camera,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
      voice: language === 'ta' ? '"நோய் கண்டறிதல்"' : language === 'hi' ? '"रोग पहचान"' : '"open disease scan"',
    },
    {
      name: t('crops'),
      desc: t('crops'),
      path: '/recommendations',
      icon: Award,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
      voice: language === 'ta' ? '"பயிர் பரிந்துரை"' : language === 'hi' ? '"فصل सुझाव"' : '"crop suggestion"',
    },
  ];

  return (
    <div className="p-4 flex flex-col gap-5 w-full animate-fade-in">

      {/* ── Farmer Profile Card ── */}
      <FarmerAvatar user={user} />

      {/* ── Voice-First Hero Banner ── */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[var(--brand-700)] to-[var(--brand-500)] p-5 text-white shadow-xl">
        <div className="absolute -top-6 -right-6 w-28 h-28 bg-white/10 rounded-full" />
        <div className="absolute -bottom-4 -left-4 w-20 h-20 bg-white/5 rounded-full" />

        <div className="relative z-10 space-y-3">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
              <Mic className="w-4 h-4" />
            </div>
            <span className="text-xs font-black uppercase tracking-widest opacity-90">
              {t('voiceConsultant')}
            </span>
          </div>

          <h2 className="text-lg font-black leading-tight">
            {localizedGreeting}, {user.username?.split(' ')[0] || user.full_name?.split(' ')[0] || 'Farmer'}! 🌾
          </h2>
          <p className="text-xs opacity-85 leading-relaxed font-semibold">
            {t('tapToAsk')}
          </p>

          <div className="flex flex-wrap gap-1.5 pt-1">
            {suggestions.map((cmd) => (
              <span
                key={cmd}
                className="text-[9px] bg-white/20 rounded-full px-2.5 py-0.5 font-bold font-sans"
              >
                {cmd}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* ── Weather Snapshot ── */}
      <div className="app-card p-4 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-sky-50 flex items-center justify-center flex-shrink-0">
          <CloudSun className="w-5 h-5 text-sky-500" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{t('weatherToday')}</div>
          <div className="text-xs font-bold text-[var(--text-900)] truncate">
            {user.location || 'Tamil Nadu, India'} · 32°C · Partly Cloudy
          </div>
        </div>
        <span className="text-[9px] bg-emerald-100 text-emerald-700 font-bold rounded-full px-2.5 py-0.5 flex-shrink-0">
          {t('good_for_farming')}
        </span>
      </div>

      {/* ── Quick Links Grid ── */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Leaf className="w-4 h-4 text-[var(--brand-600)]" />
          <h3 className="text-xs font-black text-[var(--text-900)] uppercase tracking-wider">
            {t('quickAccess')}
          </h3>
        </div>
        <div className="flex flex-col gap-3">
          {quickLinks.map(({ name, desc, path, icon: Icon, color, bg, voice }) => (
            <button
              key={path}
              onClick={() => navigate(path)}
              className="app-card p-4 flex items-center gap-3 w-full text-left active:scale-[0.98] transition-transform"
            >
              <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center flex-shrink-0`}>
                <Icon className={`w-5 h-5 ${color}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-bold text-[var(--text-900)]">{name}</div>
                <div className="text-[10px] text-gray-400 font-medium truncate">{desc}</div>
              </div>
              <div className="flex flex-col items-end gap-1 flex-shrink-0">
                <ChevronRight className="w-4 h-4 text-gray-300" />
                <span className="text-[8px] text-gray-300 font-mono">say {voice}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* ── Natural Farming Tip ── */}
      <div className="bg-[var(--beige)] rounded-2xl p-4 border border-[var(--brand-100)]">
        <div className="text-[10px] font-black uppercase tracking-widest text-[var(--brand-700)] mb-1.5">
          🌿 {t('naturalFarmingTip')}
        </div>
        <p className="text-xs text-[var(--text-700)] leading-relaxed font-semibold">
          {tipText}
        </p>
      </div>

      {/* Bottom padding for FAB */}
      <div className="h-6" />
    </div>
  );
}