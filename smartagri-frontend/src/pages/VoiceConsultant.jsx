import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage, VOICE_SUGGESTIONS } from '../context/LanguageContext';
import { Mic, Square, Volume2, Sparkles, Camera, ShieldAlert, BadgeInfo, Play, Pause, RotateCcw, Settings, X, Globe, Landmark, Cloud } from 'lucide-react';
import { getSubsidies, voiceConverse, voiceDiagnose } from '../api/voiceConsultant';
import VoiceRecorder from '../components/VoiceRecorder';
import AudioPlayer from '../components/AudioPlayer';
import API from '../api/axios';

export default function VoiceConsultant() {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const [activeTab, setActiveTab] = useState('voice'); // 'voice' | 'subsidies'
  
  // User profile
  const [user, setUser] = useState(null);

  // Profile Edit Modal State
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [editState, setEditState] = useState('');
  const [editDistrict, setEditDistrict] = useState('');
  const [editCrop, setEditCrop] = useState('');
  const [editFarmSize, setEditFarmSize] = useState('');
  const [editSoilType, setEditSoilType] = useState('');
  const [editSoilPh, setEditSoilPh] = useState('');

  // Voice Chat State
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [playingBase64, setPlayingBase64] = useState(null);
  const [playingFormat, setPlayingFormat] = useState('audio/wav');
  const [playingLocalText, setPlayingLocalText] = useState(null);
  const [isPlayingLocal, setIsPlayingLocal] = useState(false);



  // Subsidies State
  const [subsidies, setSubsidies] = useState([]);
  const [totalBenefit, setTotalBenefit] = useState(0);
  const [requiredDocs, setRequiredDocs] = useState([]);
  const [loadingSubsidies, setLoadingSubsidies] = useState(false);

  // Audio Playback
  const audioPlayerRef = useRef(null);

  useEffect(() => {
    const storedUser = localStorage.getItem('smartagri_user');
    if (storedUser) {
      const parsed = JSON.parse(storedUser);
      setUser(parsed);

      
      const profile = parsed.farmer_profile || {};
      setEditState(profile.state || parsed.state || 'Tamil Nadu');
      setEditDistrict(profile.district || parsed.district || 'Coimbatore');
      setEditCrop(profile.crop || parsed.present_crop || 'tomato');
      setEditFarmSize(profile.farm_size || parsed.land_acres || 2.0);
      setEditSoilType(profile.soil_type || parsed.soil_type || 'Red Soil');
      setEditSoilPh(profile.soil_ph || 6.5);
    }
  }, []);

  // Fetch subsidies if tab active
  useEffect(() => {
    if (activeTab === 'subsidies' && user) {
      fetchLocalSubsidies();
    }
  }, [activeTab, user]);

  const fetchLocalSubsidies = async () => {
    setLoadingSubsidies(true);
    try {
      const state = user?.farmer_profile?.state || user?.location || 'Tamil Nadu';
      const crop = user?.farmer_profile?.crop || user?.present_crop || 'tomato';
      const farmSize = user?.farmer_profile?.farm_size || user?.land_acres || 2.0;
      const data = await getSubsidies(state, crop, farmSize);
      if (data?.subsidies) {
        setSubsidies(data.subsidies);
        setTotalBenefit(data.estimated_benefit || 0);
        setRequiredDocs(data.required_documents || []);
      }
    } catch (e) {
      console.error("Failed to fetch subsidies:", e);
    } finally {
      setLoadingSubsidies(false);
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    try {
      const response = await API.put('/api/auth/profile', {
        name: user.username,
        language: language,
        state: editState,
        district: editDistrict,
        crop: editCrop,
        farm_size: parseFloat(editFarmSize),
        soil_type: editSoilType,
        soil_ph: parseFloat(editSoilPh)
      });
      
      setUser(response.data);
      localStorage.setItem('smartagri_user', JSON.stringify(response.data));

      setShowProfileModal(false);
      
      if (activeTab === 'subsidies') {
        setLoadingSubsidies(true);
        const data = await getSubsidies(editState, editCrop, editFarmSize);
        if (data?.subsidies) {
          setSubsidies(data.subsidies);
          setTotalBenefit(data.estimated_benefit || 0);
          setRequiredDocs(data.required_documents || []);
        }
        setLoadingSubsidies(false);
      }
      alert("Farmer profile updated successfully!");
    } catch (err) {
      console.error("Failed to update profile:", err);
      alert("Failed to update profile. Please try again.");
    }
  };

  // Speaks using local Web Speech API (fallback)
  const speakTextLocal = (text) => {
    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      const voices = window.speechSynthesis.getVoices();
      const matchLang = language === 'ta' ? 'ta-IN' : language === 'hi' ? 'hi-IN' : language;
      const voice = voices.find(v => v.lang.startsWith(matchLang) || v.lang.startsWith(language));
      if (voice) utterance.voice = voice;
      utterance.lang = matchLang;
      
      utterance.onstart = () => setIsPlayingLocal(true);
      utterance.onend = () => setIsPlayingLocal(false);
      utterance.onerror = () => setIsPlayingLocal(false);
      
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.error("SpeechSynthesis failed:", e);
      setIsPlayingLocal(false);
    }
  };

  // Play audio response (via backend base64 or fallback SpeechSynthesis)
  const playResponse = (audioBase64, textLocal, format = 'audio/wav') => {
    if (audioBase64) {
      setPlayingBase64(audioBase64);
      setPlayingFormat(format);
      setPlayingLocalText(null);
    } else if (textLocal) {
      setPlayingBase64(null);
      setPlayingFormat('audio/wav');
      setPlayingLocalText(textLocal);
      speakTextLocal(textLocal);
    }
  };

  // Record complete -> Converse API
  const handleRecordComplete = async (base64Audio) => {
    setIsProcessing(true);
    try {
      const response = await voiceConverse(base64Audio, language, user, false);
      
      if (response.error) {
        throw new Error(response.error);
      }

      const newMsg = {
        id: Date.now(),
        userText: response.transcribed || '...',
        agentText: response.answer_local || response.answer || '...',
        englishText: response.answer || '',
        audio: response.audio || null,
        mimeType: response.mime_type || 'audio/wav',
        action: response.action || 'AnswerOnly',
        target: response.target || null,
        suggestLabel: response.suggest_label || null,
        dataCard: response.data_card || null
      };

      setMessages(prev => [...prev, newMsg]);
      playResponse(response.audio, response.answer_local, response.mime_type || 'audio/wav');

      if (response.action === 'Navigate' && response.target) {
        setTimeout(() => {
          navigate(response.target);
        }, 1200);
      }
    } catch (err) {
      console.error("Voice converse failed:", err);
      alert("Failed to process voice. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  // Click suggestions bubble
  const handleSuggestionClick = async (suggestionText) => {
    setActiveTab('voice');
    setIsProcessing(true);
    try {
      const response = await voiceConverse("", language, user, false, suggestionText);
      
      if (response.error) {
        throw new Error(response.error);
      }

      const newMsg = {
        id: Date.now(),
        userText: response.transcribed || suggestionText,
        agentText: response.answer_local || response.answer || '...',
        englishText: response.answer || '',
        audio: response.audio || null,
        mimeType: response.mime_type || 'audio/wav',
        action: response.action || 'AnswerOnly',
        target: response.target || null,
        suggestLabel: response.suggest_label || null,
        dataCard: response.data_card || null
      };

      setMessages(prev => [...prev, newMsg]);
      playResponse(response.audio, response.answer_local, response.mime_type || 'audio/wav');

      if (response.action === 'Navigate' && response.target) {
        setTimeout(() => {
          navigate(response.target);
        }, 1200);
      }
    } catch (err) {
      console.error("Suggestion converse failed:", err);
      alert("Failed to process suggestion. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };



  // Speak all subsidies
  const speakSubsidies = () => {
    if (subsidies.length === 0) return;
    const text = subsidies.map((s, i) => `${i + 1}. ${s.name}: ${s.benefit}`).join('. ');
    speakTextLocal(text);
  };

  const stopLocalSpeech = () => {
    window.speechSynthesis.cancel();
    setIsPlayingLocal(false);
  };

  const TAB_SUGGESTIONS = {
    voice: {
      en: ["Tomato price today?", "What is the 5-layer cropping model?", "How to make Jivamrita?", "What is ZBNF?"],
      ta: ["தக்காளி விலை?", "5 அடுக்கு பயிர் முறை என்றால் என்ன?", "ஜீவாமிர்தம் செய்வது எப்படி?", "இயற்கை விவசாயம்?"],
      hi: ["टमाटर का दाम?", "5-स्तरीय खेती मॉडल क्या है?", "जीवामृत कैसे बनाएं?", "जैविक खेती क्या है?"]
    },
    subsidies: {
      en: ["Am I eligible for PM-KISAN?", "What subsidies are for organic farming?", "How to apply for seed subsidy?", "Documents for tractor subsidy?"],
      ta: ["பிஎம்-கிசானுக்கு எனக்கு தகுதி உள்ளதா?", "இயற்கை விவசாயத்திற்கான மானியங்கள்?", "விதை மானியத்திற்கு விண்ணப்பிப்பது எப்படி?", "டிராக்டர் மானியத்திற்கான ஆவணங்கள்?"],
      hi: ["क्या मैं पीएम-किसान के लिए पात्र हूँ?", "जैविक खेती के लिए कौन सी योजनाएं हैं?", "बीज सब्सिडी के लिए आवेदन कैसे करें?", "ट्रैक्टर सब्सिडी के लिए दस्तावेज?"]
    }
  };

  const getTabSuggestions = () => {
    const tabData = TAB_SUGGESTIONS[activeTab] || TAB_SUGGESTIONS['voice'];
    return tabData[language] || tabData['en'] || tabData['hi'] || tabData['ta'];
  };

  const renderDataCard = (dataCard) => {
    if (!dataCard) return null;
    
    // 1. Market Card
    if (dataCard.crop && dataCard.price && dataCard.trend) {
      return (
        <div className="mt-3 bg-emerald-50/50 border border-emerald-100 rounded-2xl p-3 text-xs space-y-2">
          <div className="flex items-center justify-between border-b border-emerald-100/50 pb-1.5">
            <span className="font-black text-emerald-950 uppercase text-[10px] tracking-wider">Mandi Price: {dataCard.crop}</span>
            <span className="bg-emerald-100 text-emerald-800 font-black text-[9px] px-1.5 py-0.5 rounded-md">{dataCard.trend}</span>
          </div>
          <div className="grid grid-cols-1 gap-1 text-gray-700">
            <div><span className="font-extrabold text-gray-900">Current Rate:</span> {dataCard.price}</div>
            <div><span className="font-extrabold text-gray-900">Best Buyer:</span> {dataCard.best_buyer}</div>
            <div className="mt-1 bg-white border border-emerald-100 p-2 rounded-xl text-emerald-800 font-bold italic">
              💡 {dataCard.recommendation}
            </div>
          </div>
        </div>
      );
    }
    
    // 2. Subsidies Card
    if (dataCard.subsidies && Array.isArray(dataCard.subsidies)) {
      return (
        <div className="mt-3 bg-blue-50/40 border border-blue-100 rounded-2xl p-3 text-xs space-y-2">
          <div className="flex items-center justify-between border-b border-blue-100/50 pb-1.5">
            <span className="font-black text-blue-950 uppercase text-[10px] tracking-wider">Government Subsidies</span>
            <span className="bg-blue-100 text-blue-800 font-black text-[9px] px-1.5 py-0.5 rounded-md">Benefit: ₹{dataCard.estimated_benefit}</span>
          </div>
          
          <div className="space-y-2">
            {dataCard.subsidies.map((sub, idx) => (
              <div key={idx} className="bg-white border border-blue-100/60 rounded-xl p-2.5 shadow-sm space-y-1">
                <div className="flex justify-between items-start gap-2">
                  <span className="font-black text-gray-900 text-xs leading-tight">{sub.name}</span>
                  <span className="bg-blue-50 text-blue-700 font-black text-[8px] px-1.5 py-0.5 rounded flex-shrink-0 uppercase">{sub.type}</span>
                </div>
                <p className="text-[11px] text-gray-600 font-semibold">{sub.benefit}</p>
                {sub.official_url && (
                  <a 
                    href={sub.official_url} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="inline-block mt-1 text-[9px] bg-blue-600 hover:bg-blue-700 text-white font-black px-2.5 py-1 rounded-lg transition-colors"
                  >
                    Apply Online →
                  </a>
                )}
              </div>
            ))}
          </div>

          {dataCard.required_documents && dataCard.required_documents.length > 0 && (
            <div className="pt-1.5 border-t border-blue-100/50 text-[10px]">
              <span className="font-bold text-blue-900 block mb-1">Required Documents:</span>
              <div className="flex flex-wrap gap-1">
                {dataCard.required_documents.map((doc, docIdx) => (
                  <span key={docIdx} className="bg-white border border-blue-100 text-gray-600 px-2 py-0.5 rounded-md font-semibold text-[9px]">
                    {doc}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }

    // 3. Weather Card
    if (dataCard.temp && dataCard.humidity && dataCard.condition) {
      return (
        <div className="mt-3 bg-amber-50/40 border border-amber-100 rounded-2xl p-3 text-xs space-y-2">
          <div className="flex items-center justify-between border-b border-amber-100/50 pb-1.5">
            <span className="font-black text-amber-950 uppercase text-[10px] tracking-wider">Weather Advisory</span>
            <span className="bg-amber-100 text-amber-800 font-black text-[9px] px-1.5 py-0.5 rounded-md">{dataCard.condition}</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-gray-700 font-semibold">
            <div>🌡 <span className="font-bold">Temp:</span> {dataCard.temp}</div>
            <div>💧 <span className="font-bold">Humidity:</span> {dataCard.humidity}</div>
          </div>
          {dataCard.organic_advisory && (
            <div className="bg-white border border-amber-100 p-2 rounded-xl text-amber-900 font-medium text-[11px] leading-relaxed">
              🚜 {dataCard.organic_advisory}
            </div>
          )}
        </div>
      );
    }

    // 4. Crop Recommendations Card
    if (dataCard.crop_name && dataCard.profit_estimate !== undefined) {
      return (
        <div className="mt-3 bg-emerald-50/50 border border-emerald-100 rounded-2xl p-3 text-xs space-y-2.5">
          <div className="flex items-center justify-between border-b border-emerald-100/50 pb-1.5">
            <span className="font-black text-emerald-950 uppercase text-[10px] tracking-wider">Next Crop Recommendation</span>
            <span className="bg-emerald-100 text-emerald-800 font-black text-[9px] px-1.5 py-0.5 rounded-md">Demand: {dataCard.market_demand_score}/10</span>
          </div>

          <div className="space-y-1">
            <div>
              <span className="font-extrabold text-gray-900">Recommended Crop:</span>{' '}
              <span className="text-emerald-700 font-black">{dataCard.crop_name}</span>
            </div>
            {dataCard.secondary_recommendation && (
              <div>
                <span className="font-extrabold text-gray-900">Secondary Option:</span>{' '}
                <span className="text-emerald-600 font-bold">{dataCard.secondary_recommendation}</span>
              </div>
            )}
            <p className="text-[11px] text-gray-600 italic mt-1 font-semibold">"{dataCard.why_suitable}"</p>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-emerald-100/50 text-[10px]">
            <div>
              <span className="font-bold text-gray-400">EST. PROFIT</span>
              <div className="text-xs font-black text-emerald-600">₹{dataCard.profit_estimate.toLocaleString()}/acre</div>
            </div>
            <div>
              <span className="font-bold text-gray-400">RISK / DURATION</span>
              <div className="text-xs font-black text-gray-700">
                Risk: {dataCard.risk_score}/10 | {dataCard.grow_duration_days} Days
              </div>
            </div>
          </div>

          {dataCard.care_tips && (
            <div className="bg-white border border-emerald-100 p-2 rounded-xl text-emerald-800 text-[11px] leading-relaxed font-medium">
              📋 <span className="font-bold">Care Tips:</span> {dataCard.care_tips}
            </div>
          )}
        </div>
      );
    }

    // 5. Disease Diagnosis Card
    if (dataCard.disease_name && dataCard.organic_remedies) {
      return (
        <div className="mt-3 bg-red-50/40 border border-red-100 rounded-2xl p-3 text-xs space-y-2">
          <div className="flex items-center justify-between border-b border-red-100/50 pb-1.5">
            <span className="font-black text-red-950 uppercase text-[10px] tracking-wider">Disease Diagnosis</span>
            <span className="bg-red-100 text-red-800 font-black text-[9px] px-1.5 py-0.5 rounded-md">{dataCard.severity_level}</span>
          </div>
          <div>
            <span className="font-extrabold text-gray-900">Disease Name:</span>{' '}
            <span className="text-red-700 font-black">{dataCard.disease_name}</span>
          </div>
          
          {dataCard.organic_remedies && dataCard.organic_remedies.length > 0 && (
            <div>
              <span className="font-bold text-emerald-800 block mb-1">🌿 Organic Remedies:</span>
              <ul className="list-disc pl-4 space-y-1 text-gray-700 font-medium">
                {dataCard.organic_remedies.map((rem, remIdx) => (
                  <li key={remIdx}>{rem}</li>
                ))}
              </ul>
            </div>
          )}

          {dataCard.prevention_steps && dataCard.prevention_steps.length > 0 && (
            <div className="pt-1.5 border-t border-red-100/50">
              <span className="font-bold text-gray-500 block mb-1">📍 Prevention Steps:</span>
              <ul className="list-disc pl-4 space-y-1 text-gray-600 font-medium">
                {dataCard.prevention_steps.map((stp, stpIdx) => (
                  <li key={stpIdx}>{stp}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      );
    }

    // 6. Natural Farming Guide Card
    if (dataCard.title && (dataCard.pillars || dataCard.ingredients || dataCard.layers || dataCard.type)) {
      return (
        <div className="mt-3 bg-amber-50/40 border border-amber-100 rounded-2xl p-3 text-xs space-y-2">
          <div className="flex items-center justify-between border-b border-amber-100/50 pb-1.5">
            <span className="font-black text-amber-950 uppercase text-[10px] tracking-wider">{dataCard.title}</span>
            <span className="bg-amber-100 text-amber-800 font-black text-[9px] px-1.5 py-0.5 rounded-md uppercase">{dataCard.type || 'Natural Farming'}</span>
          </div>
          
          <p className="text-[11px] text-gray-700 leading-relaxed font-semibold">
            {dataCard.concept || dataCard.guide_text}
          </p>

          {dataCard.pillars && (
            <ul className="list-decimal pl-4 space-y-1 text-gray-600 font-medium">
              {dataCard.pillars.map((pil, pilIdx) => (
                <li key={pilIdx}>{pil}</li>
              ))}
            </ul>
          )}

          {dataCard.ingredients && (
            <div className="bg-white border border-amber-100 p-2 rounded-xl space-y-1">
              <div><span className="font-bold text-emerald-800 text-[10px] uppercase font-black">Ingredients:</span> <p className="text-[11px] text-gray-700 font-semibold">{dataCard.ingredients}</p></div>
              {dataCard.preparation && (
                <div><span className="font-bold text-amber-800 text-[10px] uppercase font-black">Preparation:</span> <p className="text-[11px] text-gray-700 font-semibold">{dataCard.preparation}</p></div>
              )}
              {dataCard.application && (
                <div><span className="font-bold text-blue-800 text-[10px] uppercase font-black">Application:</span> <p className="text-[11px] text-gray-700 font-semibold">{dataCard.application}</p></div>
              )}
            </div>
          )}

          {dataCard.layers && (
            <div className="space-y-1.5 pt-1.5 border-t border-amber-100/50">
              <span className="font-bold text-amber-900 block text-[10px] uppercase">5-Layer Cropping Layout:</span>
              <div className="grid grid-cols-5 gap-1 text-center font-bold">
                {dataCard.layers.map((lay, layIdx) => (
                  <div key={layIdx} className="bg-white border border-amber-100 p-1 rounded-lg flex flex-col justify-between h-14">
                    <span className="text-[7px] text-amber-800 uppercase tracking-tight leading-none font-black">{lay.name || `Layer ${layIdx+1}`}</span>
                    <span className="text-[8px] text-emerald-700 font-black line-clamp-2 leading-tight">{lay.example || (lay.crops && lay.crops.join(', '))}</span>
                    <span className="text-[7px] text-gray-400 font-semibold">{lay.height || `${lay.height_feet}ft`}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="p-4 flex flex-col gap-4 animate-fade-in pb-24">
      {/* Page Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-green-800 to-emerald-600 p-6 text-white shadow-xl">
        <div className="absolute -top-4 -right-4 w-24 h-24 bg-white/10 rounded-full animate-pulse" />
        <div className="flex justify-between items-start">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-amber-300" />
            </div>
            <div>
              <h1 className="text-base font-black uppercase tracking-wider">{t('voiceConsultant')}</h1>
              <p className="text-xs opacity-80 font-medium">ZBNF Natural Farming Assistant</p>
            </div>
          </div>
          <button 
            onClick={() => setShowProfileModal(true)} 
            className="w-10 h-10 rounded-2xl bg-white/20 hover:bg-white/30 backdrop-blur flex items-center justify-center transition-colors"
            title="Farmer Profile Settings"
          >
            <Settings className="w-5 h-5 text-white" />
          </button>
        </div>
        <p className="text-xs opacity-90 leading-relaxed font-semibold mt-2">
          Access organic remedies, mandi pricing, government schemes, and crop education directly by speaking or scanning.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex bg-white border border-[var(--line)] rounded-2xl p-1 shadow-sm">
        <button
          onClick={() => { setActiveTab('voice'); stopLocalSpeech(); }}
          className={`flex-1 py-2.5 text-xs font-black rounded-xl transition-all ${
            activeTab === 'voice' ? 'bg-emerald-600 text-white shadow-md' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {t('voiceConsultant').split(' ')[0]}
        </button>
        <button
          onClick={() => { setActiveTab('subsidies'); stopLocalSpeech(); }}
          className={`flex-1 py-2.5 text-xs font-black rounded-xl transition-all ${
            activeTab === 'subsidies' ? 'bg-emerald-600 text-white shadow-md' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {t('govtSchemes').split(' ')[0]}
        </button>
      </div>

      {/* Tab Contents */}
      {activeTab === 'voice' && (
        <div className="flex flex-col gap-4 animate-fade-in">
          {/* Quick Suggestions Bubbles */}
          <div className="flex flex-col gap-1.5">
            <span className="text-[10px] font-black uppercase tracking-widest text-[var(--brand-700)] px-1">
              Suggestions
            </span>
            <div className="flex flex-wrap gap-1.5">
              {getTabSuggestions().map((cmd) => (
                <button
                  key={cmd}
                  onClick={() => handleSuggestionClick(cmd)}
                  className="text-[10px] bg-white border border-emerald-100 hover:border-emerald-300 font-bold rounded-full px-3 py-1.5 shadow-sm text-gray-700 transition-colors"
                >
                  "{cmd}"
                </button>
              ))}
            </div>
          </div>

          {/* Conversation History Card */}
          <div className="app-card p-4 min-h-[160px] flex flex-col gap-3">
            <h3 className="text-xs font-black uppercase tracking-widest text-gray-400">Discussion History</h3>
            
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-6 text-gray-400 gap-1 flex-1">
                <Mic className="w-8 h-8 text-gray-300" />
                <span className="text-xs font-semibold">{t('tapToAsk')}</span>
              </div>
            ) : (
              <div className="flex flex-col gap-3 max-h-[300px] overflow-y-auto pr-1">
                {messages.map((msg) => (
                  <div key={msg.id} className="space-y-2 border-b border-gray-100 pb-3 last:border-0 last:pb-0">
                    <div className="flex items-start gap-2">
                      <span className="text-[9px] font-black text-emerald-800 bg-emerald-50 rounded px-1.5 py-0.5 mt-0.5 flex-shrink-0">YOU</span>
                      <p className="text-xs text-gray-700 font-bold italic">"{msg.userText}"</p>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-[9px] font-black text-amber-800 bg-amber-50 rounded px-1.5 py-0.5 mt-0.5 flex-shrink-0">AI</span>
                      <div className="flex-1">
                        <p className="text-xs text-gray-900 font-bold leading-relaxed">{msg.agentText}</p>
                        
                        {/* Zero English Leakage Translation */}
                        {language === 'en' && msg.englishText && msg.englishText !== msg.agentText && (
                          <p className="text-[9px] text-gray-400 font-semibold mt-0.5">{msg.englishText}</p>
                        )}
                        
                        {/* Optional inline navigation button */}
                        {msg.action === 'AnswerAndSuggestNavigation' && msg.target && (
                          <button
                            onClick={() => navigate(msg.target)}
                            className="mt-2 bg-emerald-600 hover:bg-emerald-700 text-white font-black text-[10px] rounded-xl px-3 py-1.5 shadow-sm inline-flex items-center gap-1 transition-all"
                          >
                            <span>{msg.suggestLabel || 'View Details'}</span>
                            <Sparkles className="w-3 h-3 text-amber-300 animate-pulse" />
                          </button>
                        )}

                        {/* Inline Data Card */}
                        {renderDataCard(msg.dataCard)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Voice input card */}
          <div className="flex flex-col gap-2">
            <span className="text-[10px] font-black uppercase tracking-widest text-[var(--brand-700)] px-1">
              Voice Trigger
            </span>
            <VoiceRecorder 
              onRecordComplete={handleRecordComplete} 
              isProcessing={isProcessing} 
            />
          </div>
        </div>
      )}

      {activeTab === 'subsidies' && (
        <div className="flex flex-col gap-4 animate-fade-in">
          {/* Quick Suggestions Bubbles */}
          <div className="flex flex-col gap-1.5">
            <span className="text-[10px] font-black uppercase tracking-widest text-[var(--brand-700)] px-1">
              Suggestions
            </span>
            <div className="flex flex-wrap gap-1.5">
              {getTabSuggestions().map((cmd) => (
                <button
                  key={cmd}
                  onClick={() => handleSuggestionClick(cmd)}
                  className="text-[10px] bg-white border border-emerald-100 hover:border-emerald-300 font-bold rounded-full px-3 py-1.5 shadow-sm text-gray-700 transition-colors"
                >
                  "{cmd}"
                </button>
              ))}
            </div>
          </div>

          {/* Subsidies listing */}
          <div className="app-card p-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xs font-black uppercase tracking-widest text-[var(--brand-700)]">Government Subsidies</h3>
                <p className="text-[9px] text-gray-400 font-medium">Recommended for {user?.farmer_profile?.state || user?.location || 'Tamil Nadu'}</p>
              </div>

              {subsidies.length > 0 && (
                <button
                  onClick={isPlayingLocal ? stopLocalSpeech : speakSubsidies}
                  className="bg-emerald-50 border border-emerald-200 text-emerald-700 font-bold text-[10px] rounded-xl px-3 py-1.5 flex items-center gap-1 transition-colors hover:bg-emerald-100"
                >
                  <Volume2 className="w-3.5 h-3.5" />
                  {isPlayingLocal ? 'Stop' : 'Speak Schemes'}
                </button>
              )}
            </div>

            {loadingSubsidies ? (
              <div className="text-center py-6 text-xs text-gray-400 font-bold animate-pulse">
                Fetching regional schemes...
              </div>
            ) : subsidies.length === 0 ? (
              <div className="text-center py-6 text-xs text-gray-400 font-bold">
                No subsidies found for your region.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-3 flex justify-between items-center text-xs">
                  <span className="font-extrabold text-emerald-900">Total Potential Benefit:</span>
                  <span className="font-black text-emerald-700 text-sm">₹{totalBenefit.toLocaleString()}</span>
                </div>

                <div className="flex flex-col gap-3">
                  {subsidies.map((sub, i) => (
                    <div key={i} className="border border-gray-100 rounded-2xl p-3.5 hover:border-emerald-100 transition-colors bg-gray-50/50 space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-xs font-black text-gray-900 leading-tight">{sub.name}</h4>
                        <span className="text-[8px] bg-emerald-100 text-emerald-700 font-black px-1.5 py-0.5 rounded-lg flex-shrink-0 uppercase">{sub.type}</span>
                      </div>
                      <p className="text-xs font-semibold text-[var(--brand-700)]">Benefit: {sub.benefit}</p>
                      <p className="text-[11px] text-gray-600 font-medium">Eligibility: {sub.eligibility}</p>
                      
                      <div className="flex items-center justify-between border-t border-gray-100 pt-2 text-[10px] font-bold">
                        <span className="text-gray-400">Apply: {sub.how_to_apply || 'Online'}</span>
                        {sub.official_url && (
                          <a 
                            href={sub.official_url} 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            className="text-emerald-600 hover:text-emerald-700"
                          >
                            Official Website →
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {requiredDocs.length > 0 && (
                  <div className="pt-2 border-t border-gray-100">
                    <span className="block text-[10px] font-black uppercase text-gray-400 mb-1.5">Required Documents Checklist:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {requiredDocs.map((doc, i) => (
                        <span key={i} className="bg-gray-100 text-gray-700 rounded-lg px-2.5 py-1 text-[10px] font-bold border border-gray-200">
                          {doc}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Global Active Audio Players */}
      {playingBase64 && (
        <div className="bg-white border border-gray-150 rounded-2xl p-3 shadow-md mt-2">
          <span className="text-[9px] font-black text-emerald-850 uppercase tracking-widest mb-1.5 block">Audio Player</span>
          <AudioPlayer audioBase64={playingBase64} audioFormat={playingFormat} />
        </div>
      )}

      {playingLocalText && (
        <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-3 flex items-center justify-between shadow-sm animate-pulse mt-2">
          <div className="flex items-center gap-2">
            <Volume2 className="w-4 h-4 text-emerald-600 animate-bounce" />
            <span className="text-xs font-bold text-emerald-800">Speaking Advisory...</span>
          </div>
          {isPlayingLocal && (
            <button
              onClick={stopLocalSpeech}
              className="text-[10px] font-black text-red-600 hover:text-red-700"
            >
              Stop Voice
            </button>
          )}
        </div>
      )}

      {/* Farmer Profile Settings Modal */}
      {showProfileModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-3xl w-full max-w-md overflow-hidden shadow-2xl border border-gray-100 flex flex-col max-h-[90vh]">
            <div className="bg-emerald-800 text-white px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-amber-300 animate-pulse" />
                <h2 className="text-sm font-black uppercase tracking-wider">Farmer Profile Settings</h2>
              </div>
              <button 
                onClick={() => setShowProfileModal(false)}
                className="p-1.5 rounded-full hover:bg-white/20 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleProfileUpdate} className="p-6 flex-1 overflow-y-auto space-y-4">
              <div>
                <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">State</label>
                <input
                  type="text"
                  value={editState}
                  onChange={(e) => setEditState(e.target.value)}
                  required
                  className="w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-xs outline-none bg-gray-50/50 focus:border-emerald-600 focus:bg-white transition-all font-semibold"
                />
              </div>

              <div>
                <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">District</label>
                <input
                  type="text"
                  value={editDistrict}
                  onChange={(e) => setEditDistrict(e.target.value)}
                  required
                  className="w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-xs outline-none bg-gray-50/50 focus:border-emerald-600 focus:bg-white transition-all font-semibold"
                />
              </div>

              <div>
                <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">Present Crop</label>
                <input
                  type="text"
                  value={editCrop}
                  onChange={(e) => setEditCrop(e.target.value)}
                  required
                  className="w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-xs outline-none bg-gray-50/50 focus:border-emerald-600 focus:bg-white transition-all font-semibold"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">Farm Size (Acres)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editFarmSize}
                    onChange={(e) => setEditFarmSize(e.target.value)}
                    required
                    className="w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-xs outline-none bg-gray-50/50 focus:border-emerald-600 focus:bg-white transition-all font-semibold"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">Soil pH</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editSoilPh}
                    onChange={(e) => setEditSoilPh(e.target.value)}
                    required
                    className="w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-xs outline-none bg-gray-50/50 focus:border-emerald-600 focus:bg-white transition-all font-semibold"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">Soil Type</label>
                <select
                  value={editSoilType}
                  onChange={(e) => setEditSoilType(e.target.value)}
                  required
                  className="w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-xs outline-none bg-gray-50/50 focus:border-emerald-600 focus:bg-white transition-all font-semibold"
                >
                  <option value="Red Soil">Red Soil</option>
                  <option value="Black Soil">Black Soil</option>
                  <option value="Alluvial Soil">Alluvial Soil</option>
                  <option value="Clayey Soil">Clayey Soil</option>
                  <option value="Sandy Soil">Sandy Soil</option>
                  <option value="Loamy Soil">Loamy Soil</option>
                  <option value="Laterite Soil">Laterite Soil</option>
                </select>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl py-3 text-xs font-black shadow-md flex items-center justify-center gap-1.5 transition-colors"
                >
                  Save Profile Settings
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}