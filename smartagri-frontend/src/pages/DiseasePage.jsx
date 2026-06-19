import React, { useState, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { Camera, ShieldAlert, Volume2, Sparkles, X, Activity, Leaf, Shield, Check, Info } from 'lucide-react';
import { voiceDiagnose, voiceConverse } from '../api/voiceConsultant';
import AudioPlayer from '../components/AudioPlayer';

export default function DiseasePage() {
  const { language, t } = useLanguage();
  
  // User context
  const [user, setUser] = useState(null);
  const [cropContext, setCropContext] = useState('');

  // Diagnostic states
  const [imagePreview, setImagePreview] = useState(null);
  const [isDiagnosing, setIsDiagnosing] = useState(false);
  const [diagnosisResult, setDiagnosisResult] = useState(null);

  // In-place follow up conversation states
  const [isProcessingFollowUp, setIsProcessingFollowUp] = useState(false);
  const [followUpResponse, setFollowUpResponse] = useState(null); // { query: '', text: '' }

  // Audio Playback
  const [playingBase64, setPlayingBase64] = useState(null);
  const [playingFormat, setPlayingFormat] = useState('audio/wav');
  const [playingLocalText, setPlayingLocalText] = useState(null);
  const [isPlayingLocal, setIsPlayingLocal] = useState(false);

  useEffect(() => {
    const storedUser = localStorage.getItem('smartagri_user');
    if (storedUser) {
      const parsed = JSON.parse(storedUser);
      setUser(parsed);
      setCropContext(parsed.present_crop || parsed.farmer_profile?.crop || '');
    }
  }, []);

  // Web Speech API synthesis fallback
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
      console.error("Local speech synthesis failed:", e);
      setIsPlayingLocal(false);
    }
  };

  const stopLocalSpeech = () => {
    window.speechSynthesis.cancel();
    setIsPlayingLocal(false);
  };

  const playResponse = (audioBase64, textLocal, format = 'audio/wav') => {
    // Cancel any active speechSynthesis
    window.speechSynthesis.cancel();
    setIsPlayingLocal(false);

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

  // Image Upload handler
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
        setDiagnosisResult(null);
        setFollowUpResponse(null);
        setPlayingBase64(null);
        setPlayingLocalText(null);
        stopLocalSpeech();
      };
      reader.readAsDataURL(file);
    }
  };

  // Diagnose leaf submission
  const handleDiagnose = async () => {
    if (!imagePreview) return;
    setIsDiagnosing(true);
    setDiagnosisResult(null);
    setFollowUpResponse(null);
    setPlayingBase64(null);
    setPlayingLocalText(null);
    stopLocalSpeech();

    try {
      const base64Image = imagePreview.split(',')[1];
      const res = await voiceDiagnose(base64Image, language, cropContext);
      setDiagnosisResult(res);
      
      // Speak the diagnosis aloud
      playResponse(res.audio, res.translated_answer || res.disease_name, res.mime_type || 'audio/wav');
    } catch (e) {
      console.error("Leaf diagnosis failed:", e);
      alert("Failed to analyze image. Please try again.");
    } finally {
      setIsDiagnosing(false);
    }
  };

  // Disease conversational follow-ups in-place
  const handleDiseaseFollowUp = async (type) => {
    if (!diagnosisResult) return;
    const diseaseName = diagnosisResult.disease_name;
    let textQuery = "";
    
    if (type === 'remedy') {
      textQuery = `Give organic remedy for ${diseaseName}`;
    } else if (type === 'prevention') {
      textQuery = `What is the prevention plan for ${diseaseName}`;
    } else if (type === 'severity') {
      textQuery = `Explain severity of ${diseaseName}`;
    }
    
    setIsProcessingFollowUp(true);
    setPlayingBase64(null);
    setPlayingLocalText(null);
    stopLocalSpeech();

    try {
      const response = await voiceConverse("", language, user, false, textQuery);
      if (response.error) throw new Error(response.error);
      
      setFollowUpResponse({
        query: textQuery,
        text: response.answer_local || response.answer || '...'
      });

      playResponse(response.audio, response.answer_local, response.mime_type || 'audio/wav');
    } catch (e) {
      console.error("Disease follow-up failed:", e);
      alert("Failed to get response. Please try again.");
    } finally {
      setIsProcessingFollowUp(false);
    }
  };

  // Dynamic style helper for severity badge
  const getSeverityStyle = (level) => {
    const lvl = (level || 'moderate').toLowerCase();
    if (lvl.includes('high') || lvl.includes('severe')) {
      return 'bg-red-100 text-red-700 border-red-200';
    }
    if (lvl.includes('low') || lvl.includes('mild')) {
      return 'bg-emerald-100 text-emerald-700 border-emerald-200';
    }
    return 'bg-amber-100 text-amber-700 border-amber-200';
  };

  return (
    <div className="p-4 flex flex-col gap-4 animate-fade-in pb-24">
      {/* Page Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-800 to-teal-600 p-6 text-white shadow-xl">
        <div className="absolute -top-4 -right-4 w-24 h-24 bg-white/10 rounded-full animate-pulse" />
        <div className="flex justify-between items-start">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
              <Camera className="w-6 h-6 text-amber-300" />
            </div>
            <div>
              <h1 className="text-base font-black uppercase tracking-wider">{t('diseaseScan')}</h1>
              <p className="text-xs opacity-95 font-medium">AI Leaf Diagnostics & Organic Remedies</p>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Leaf Input Card */}
      <div className="bg-white border border-[var(--line)] rounded-3xl p-5 flex flex-col gap-4 shadow-sm">
        <h3 className="text-xs font-black uppercase tracking-widest text-gray-400">Scan Crop Leaf</h3>
        
        <div className="flex flex-col items-center gap-3">
          <div className="relative w-full h-44 border-2 border-dashed border-gray-200 hover:border-emerald-400 transition-colors rounded-2xl flex flex-col items-center justify-center bg-gray-50/50 overflow-hidden group cursor-pointer">
            {imagePreview ? (
              <img src={imagePreview} alt="Leaf Preview" className="w-full h-full object-cover" />
            ) : (
              <div className="flex flex-col items-center gap-2 text-gray-400">
                <Camera className="w-10 h-10 text-emerald-600/70 animate-pulse" />
                <span className="text-xs font-bold text-gray-500">Take a photo or select image</span>
                <span className="text-[10px] text-gray-400">Supports JPG, PNG</span>
              </div>
            )}
            <input
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              className="absolute inset-0 opacity-0 cursor-pointer"
            />
          </div>

          {/* Crop Context input */}
          <div className="w-full">
            <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1 px-1">
              Crop Context
            </label>
            <input
              type="text"
              value={cropContext}
              onChange={(e) => setCropContext(e.target.value)}
              placeholder="e.g. Tomato, Paddy, Onion"
              className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-xs outline-none bg-gray-50/50 font-semibold focus:border-emerald-600 focus:bg-white transition-all"
            />
          </div>

          <button
            onClick={handleDiagnose}
            disabled={!imagePreview || isDiagnosing}
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl py-3 text-xs font-black shadow-md flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
          >
            {isDiagnosing ? 'Running Crop Vision Analysis...' : 'Diagnose Plant Disease'}
          </button>
        </div>
      </div>

      {/* Visualizer/Loading overlay inside page */}
      {isDiagnosing && (
        <div className="bg-white/80 border border-emerald-100 rounded-3xl p-8 flex flex-col items-center justify-center gap-3 shadow-md animate-pulse">
          <Activity className="w-8 h-8 text-emerald-600 animate-spin" />
          <span className="text-xs font-bold text-gray-600">Analyzing leaf cell structures...</span>
          <span className="text-[10px] text-gray-400">Identifying pests & disease symptoms</span>
        </div>
      )}

      {/* Diagnosis results card */}
      {diagnosisResult && (
        <div className="bg-white rounded-3xl border border-[var(--line)] shadow-sm overflow-hidden animate-fade-in flex flex-col">
          <div className={`px-4 py-3 flex items-center justify-between border-b ${getSeverityStyle(diagnosisResult.severity_level)}`}>
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4" />
              <span className="text-xs font-black uppercase tracking-wider">{diagnosisResult.disease_name}</span>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider border rounded-full px-2.5 py-0.5">
              Severity: {diagnosisResult.severity_level || 'Moderate'}
            </span>
          </div>
          
          <div className="p-4 space-y-4">
            {/* Organic Remedies */}
            <div className="bg-emerald-50/30 border border-emerald-100/50 rounded-2xl p-3.5">
              <h4 className="text-[10px] font-black uppercase tracking-wider text-emerald-800 mb-2 flex items-center gap-1">
                <Leaf className="w-3.5 h-3.5" /> Organic Remedies
              </h4>
              <ul className="space-y-1.5">
                {diagnosisResult.organic_remedies?.map((rem, i) => (
                  <li key={i} className="text-xs font-bold text-gray-700 flex items-start gap-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-600 mt-0.5 flex-shrink-0" />
                    <span>{rem}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Prevention Steps */}
            <div className="bg-gray-50 border border-gray-150 rounded-2xl p-3.5">
              <h4 className="text-[10px] font-black uppercase tracking-wider text-gray-400 mb-2 flex items-center gap-1">
                <Shield className="w-3.5 h-3.5 text-gray-400" /> Prevention Steps
              </h4>
              <ul className="space-y-1.5">
                {diagnosisResult.prevention_steps?.map((step, i) => (
                  <li key={i} className="text-xs font-bold text-gray-650 flex items-start gap-1.5">
                    <span className="text-amber-500 mt-0.5 font-bold">•</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Interactive follow-up buttons */}
            <div className="flex flex-wrap gap-2 pt-3 border-t border-gray-100">
              <button
                onClick={() => handleDiseaseFollowUp('remedy')}
                disabled={isProcessingFollowUp}
                className="flex-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-850 font-black text-[10px] rounded-xl py-2.5 px-2.5 transition-all text-center border border-emerald-100 shadow-sm disabled:opacity-50"
              >
                🌿 Organic Remedy
              </button>
              <button
                onClick={() => handleDiseaseFollowUp('prevention')}
                disabled={isProcessingFollowUp}
                className="flex-1 bg-amber-50 hover:bg-amber-100 text-amber-850 font-black text-[10px] rounded-xl py-2.5 px-2.5 transition-all text-center border border-amber-100 shadow-sm disabled:opacity-50"
              >
                🛡 Prevention Plan
              </button>
              <button
                onClick={() => handleDiseaseFollowUp('severity')}
                disabled={isProcessingFollowUp}
                className="flex-1 bg-red-50 hover:bg-red-100 text-red-850 font-black text-[10px] rounded-xl py-2.5 px-2.5 transition-all text-center border border-red-100 shadow-sm disabled:opacity-50"
              >
                ⚠️ Severity Details
              </button>
            </div>
          </div>
        </div>
      )}

      {/* In-place speech bubble/follow-up response */}
      {(isProcessingFollowUp || followUpResponse) && (
        <div className="bg-white border border-emerald-100 rounded-3xl p-4 shadow-md animate-fade-in flex flex-col gap-2 relative">
          {followUpResponse && (
            <button
              onClick={() => setFollowUpResponse(null)}
              className="absolute top-2 right-2 p-1.5 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <div className="flex flex-col gap-0.5 border-b border-gray-100 pb-1.5">
            <span className="text-[9px] font-black uppercase tracking-wider text-emerald-600">Question</span>
            <p className="text-xs font-semibold text-gray-750 italic">
              "{isProcessingFollowUp ? 'Asking KisanAI...' : followUpResponse?.query}"
            </p>
          </div>

          <div className="flex flex-col gap-1">
            <span className="text-[9px] font-black uppercase tracking-wider text-emerald-600 flex items-center gap-1">
              <Volume2 className="w-3.5 h-3.5 animate-pulse" /> Krishi AI Response
            </span>
            {isProcessingFollowUp ? (
              <span className="text-xs font-bold text-gray-400 animate-pulse">Generating advisory reply...</span>
            ) : (
              <p className="text-xs font-bold text-gray-850 leading-relaxed">{followUpResponse?.text}</p>
            )}
          </div>
        </div>
      )}

      {/* Global Active Audio Players */}
      {playingBase64 && (
        <div className="bg-white border border-gray-150 rounded-2xl p-3 shadow-md">
          <span className="text-[9px] font-black text-emerald-850 uppercase tracking-widest mb-1.5 block">
            Voice Advisory Player
          </span>
          <AudioPlayer audioBase64={playingBase64} audioFormat={playingFormat} />
        </div>
      )}

      {playingLocalText && (
        <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-3 flex items-center justify-between shadow-sm animate-pulse">
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
    </div>
  );
}
