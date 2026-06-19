import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, Square, Volume2, X, RefreshCw, AlertCircle } from 'lucide-react';
import { getLanguages, prefetchLanguages, voiceConverse } from '../api/voiceConsultant';
import { useLanguage } from '../context/LanguageContext';

export default function VoiceAssistantFAB() {
  const navigate = useNavigate();

  const { language: selectedLang, changeLanguage, t } = useLanguage();
  const [languages, setLanguages] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  
  // Dialog / Toast state
  const [dialogue, setDialogue] = useState(null); // { userText: '', agentText: '', nativeAgentText: '' }
  const [showBubble, setShowBubble] = useState(false);
  const [errorText, setErrorText] = useState('');

  // Audio recording refs (Pure JS WAV Encoder)
  const audioContextInstanceRef = useRef(null);
  const scriptProcessorRef = useRef(null);
  const sourceRef = useRef(null);
  const leftchannel = useRef([]);
  const recordingLength = useRef(0);
  const sampleRate = useRef(16000);
  const mediaStreamRef = useRef(null);

  // Audio Context for visualizer
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  
  // HTML5 audio playback ref
  const audioPlayerRef = useRef(null);
  const [audioUrl, setAudioUrl] = useState('');
  
  // Dynamic visualizer bars
  const [visualizerBars, setVisualizerBars] = useState(new Array(10).fill(4));

  useEffect(() => {
    loadLanguages();
    return () => {
      stopVisualizer();
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, []);

  const loadLanguages = async () => {
    try {
      const data = await getLanguages();
      if (data?.languages) {
        setLanguages(data.languages);
      }
    } catch (e) {
      console.error("Failed to load languages:", e);
    }
  };

  const handleLanguageChange = (e) => {
    const code = e.target.value;
    changeLanguage(code);
    prefetchLanguages(code).catch(console.error);
  };

  // ── Visualizer Wave ──
  const startVisualizer = (stream) => {
    try {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 32;
      source.connect(analyserRef.current);
      
      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      const updateWave = () => {
        analyserRef.current.getByteFrequencyData(dataArray);
        
        // Map frequencies to height values
        const bars = Array.from(dataArray).slice(0, 10).map(val => {
          const height = Math.max(4, Math.floor((val / 255) * 28));
          return height;
        });
        setVisualizerBars(bars);
        animationFrameRef.current = requestAnimationFrame(updateWave);
      };
      
      updateWave();
    } catch (err) {
      console.error("Visualizer setup failed:", err);
    }
  };

  const stopVisualizer = () => {
    if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
    }
    setVisualizerBars(new Array(10).fill(4));
  };

  // Helper WAV buffer merge
  const mergeBuffers = (channelBuffer, length) => {
    const result = new Float32Array(length);
    let offset = 0;
    for (let i = 0; i < channelBuffer.length; i++) {
      const buffer = channelBuffer[i];
      result.set(buffer, offset);
      offset += buffer.length;
    }
    return result;
  };

  // Helper write text bytes
  const writeUTFBytes = (view, offset, string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  // Helper encode PCM samples to WAV Blob
  const encodeWAV = (samples, recordingSampleRate) => {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    writeUTFBytes(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeUTFBytes(view, 8, 'WAVE');
    writeUTFBytes(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, recordingSampleRate, true);
    view.setUint32(28, recordingSampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeUTFBytes(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);

    let offset = 44;
    for (let i = 0; i < samples.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }

    return new Blob([view], { type: 'audio/wav' });
  };

  // ── Native WAV audio recording ──
  const startRecording = async () => {
    if (window.location.pathname !== '/voice-consultant') {
      navigate('/voice-consultant');
      setTimeout(() => {
        startRecordingActual();
      }, 300);
    } else {
      startRecordingActual();
    }
  };

  const startRecordingActual = async () => {
    setErrorText('');
    leftchannel.current = [];
    recordingLength.current = 0;
    
    // Stop any active playing audio
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      setIsPlaying(false);
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const AudioContext = window.AudioContext || window.webkitAudioContext;
      const audioContext = new AudioContext({ sampleRate: 16000 });
      audioContextInstanceRef.current = audioContext;
      sampleRate.current = audioContext.sampleRate;

      sourceRef.current = audioContext.createMediaStreamSource(stream);
      scriptProcessorRef.current = audioContext.createScriptProcessor(2048, 1, 1);
      
      scriptProcessorRef.current.onaudioprocess = (e) => {
        const left = e.inputBuffer.getChannelData(0);
        leftchannel.current.push(new Float32Array(left));
        recordingLength.current += left.length;
      };

      sourceRef.current.connect(scriptProcessorRef.current);
      scriptProcessorRef.current.connect(audioContext.destination);

      setIsRecording(true);
      startVisualizer(stream);
    } catch (err) {
      console.error("Mic access denied:", err);
      setErrorText("Microphone access denied or unsupported.");
    }
  };

  const stopRecording = () => {
    if (!isRecording) return;
    setIsRecording(false);
    stopVisualizer();

    if (scriptProcessorRef.current) {
      scriptProcessorRef.current.disconnect();
      scriptProcessorRef.current = null;
    }
    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }
    if (audioContextInstanceRef.current) {
      audioContextInstanceRef.current.close().catch(() => {});
      audioContextInstanceRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }

    // Process and send the WAV file
    const leftBuffer = mergeBuffers(leftchannel.current, recordingLength.current);
    const wavBlob = encodeWAV(leftBuffer, sampleRate.current);

    const reader = new FileReader();
    reader.readAsDataURL(wavBlob);
    reader.onloadend = async () => {
      const base64Audio = reader.result.split(',')[1];
      await submitVoiceCommand(base64Audio);
    };
  };

  // ── Send base64 audio or text query to unified voice-consultant endpoint ──
  const submitVoiceCommand = async (base64Audio, textQuery = "") => {
    setIsProcessing(true);
    setErrorText('');
    try {
      const storedUser = localStorage.getItem('smartagri_user');
      const profile = storedUser ? JSON.parse(storedUser) : null;
      
      const response = await voiceConverse(base64Audio, selectedLang, profile, false, textQuery);
      
      if (response.error) {
        throw new Error(response.error);
      }

      setDialogue({
        userText: response.transcribed || textQuery || '...',
        agentText: response.answer || '...',
        nativeAgentText: response.answer_local || '...'
      });
      setShowBubble(true);

      // Play audio response
      if (response.audio) {
        const audioBytes = Uint8Array.from(atob(response.audio), c => c.charCodeAt(0));
        const mimeType = response.mime_type || 'audio/wav';
        const audioBlob = new Blob([audioBytes], { type: mimeType });
        if (audioUrl) URL.revokeObjectURL(audioUrl);
        const newUrl = URL.createObjectURL(audioBlob);
        setAudioUrl(newUrl);
        
        setIsPlaying(true);
        setTimeout(() => {
          if (audioPlayerRef.current) {
            audioPlayerRef.current.src = newUrl;
            audioPlayerRef.current.play().catch(e => {
              console.error("Audio playback blocked/failed:", e);
              setIsPlaying(false);
            });
          }
        }, 100);
      } else if (response.answer_local) {
        // Fallback to browser SpeechSynthesis
        setIsPlaying(true);
        try {
          window.speechSynthesis.cancel();
          const utterance = new SpeechSynthesisUtterance(response.answer_local);
          const voices = window.speechSynthesis.getVoices();
          const matchLang = selectedLang === 'ta' ? 'ta-IN' : selectedLang === 'hi' ? 'hi-IN' : selectedLang;
          const voice = voices.find(v => v.lang.startsWith(matchLang) || v.lang.startsWith(selectedLang));
          if (voice) {
            utterance.voice = voice;
          }
          utterance.lang = matchLang;
          utterance.onend = () => setIsPlaying(false);
          utterance.onerror = () => setIsPlaying(false);
          window.speechSynthesis.speak(utterance);
        } catch (e) {
          console.error("SpeechSynthesis failed:", e);
          setIsPlaying(false);
        }
      }

      // Handle Page Navigation action (case-insensitive)
      const actionLower = response.action ? response.action.toLowerCase() : '';
      if (actionLower === 'navigate' && response.target) {
        setTimeout(() => {
          navigate(response.target);
        }, 1200); // Small delay to let user hear confirmation
      }
    } catch (err) {
      console.error("Voice processing failed:", err);
      setErrorText("Could not understand the audio. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  const PATH_SUGGESTIONS = {
    market: {
      en: ["Tomato price today?", "Who is buying paddy?", "Hold or sell tomatoes?"],
      ta: ["தக்காளி விலை?", "நெல் வாங்குபவர் யார்?", "தக்காளி விற்கலாமா?"],
      hi: ["टमाटर का दाम?", "धान कौन खरीद रहा है?", "टमाटर रोकें या बेचें?"]
    },
    pest: {
      en: ["Remedy for early blight?", "Neem oil spray dosage?", "Stem borer prevention?"],
      ta: ["ஆர்லி ப்லைட் தீர்வு?", "வேப்ப எண்ணெய் அளவு?", "தண்டு துளைப்பான் தடுப்பு?"],
      hi: ["अगेती झुलसा का उपाय?", "नीम के तेल की मात्रा?", "तना छेदक से बचाव?"]
    },
    recommendations: {
      en: ["What crop to grow next?", "Best crop for red soil?", "High profit crops?"],
      ta: ["அடுத்து என்ன பயிர்?", "செம்மண்ணுக்கு ஏற்ற பயிர்?", "அதிக லாப பயிர்கள்?"],
      hi: ["अगली फसल कौन सी लगाएं?", "लाल मिट्टी के लिए बेस्ट फसल?", "अधिक मुनाफे वाली फसल?"]
    },
    default: {
      en: ["Tomato price today?", "How to make Jivamrita?", "What is ZBNF?"],
      ta: ["தக்காளி விலை?", "ஜீவாமிர்தம் செய்வது எப்படி?", "இயற்கை விவசாயம்?"],
      hi: ["टमाटर का दाम?", "जीवामृत कैसे बनाएं?", "जैविक खेती क्या है?"]
    }
  };

  const getPathCategory = () => {
    const path = window.location.pathname.toLowerCase();
    if (path.includes('market')) return 'market';
    if (path.includes('pest') || path.includes('disease') || path.includes('diagnose')) return 'pest';
    if (path.includes('recommend') || path.includes('crop')) return 'recommendations';
    return 'default';
  };

  const getSuggestions = () => {
    const cat = getPathCategory();
    const suggestionsForCat = PATH_SUGGESTIONS[cat] || PATH_SUGGESTIONS['default'];
    return suggestionsForCat[selectedLang] || suggestionsForCat['en'] || suggestionsForCat['hi'] || suggestionsForCat['ta'];
  };

  return (
    <div className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[480px] z-50 flex flex-col items-center select-none pointer-events-none pb-[calc(14px+env(safe-area-inset-bottom))]">
      
      {/* ── Dialogue/Transcript Bubble ── */}
      {showBubble && dialogue && (
        <div className="bg-white/95 backdrop-blur-md border border-emerald-100 rounded-3xl p-4 shadow-2xl w-[90%] max-w-[360px] text-left animate-fade-in flex flex-col gap-2 relative pointer-events-auto mb-2">
          <button 
            onClick={() => setShowBubble(false)} 
            className="absolute top-2 right-2 p-1 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100"
          >
            <X className="w-3.5 h-3.5" />
          </button>
          
          <div className="flex flex-col gap-1 border-b border-gray-100 pb-2">
            <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-600">You said</span>
            <p className="text-xs text-gray-700 font-medium italic">"{dialogue.userText}"</p>
          </div>
          
          <div className="flex flex-col gap-1">
            <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-600 flex items-center gap-1">
              <Volume2 className="w-3 h-3 animate-pulse" /> Krishi Advisor
            </span>
            <p className="text-sm text-gray-900 font-bold leading-relaxed">{dialogue.nativeAgentText}</p>
            
            {/* Zero English Leakage */}
            {selectedLang === 'en' && dialogue.agentText !== dialogue.nativeAgentText && (
              <p className="text-[10px] text-gray-400 font-medium">{dialogue.agentText}</p>
            )}
          </div>
        </div>
      )}

      {/* ── Error Toast ── */}
      {errorText && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs px-4 py-2 rounded-xl shadow-lg flex items-center gap-2 animate-bounce pointer-events-auto mb-2">
          <AlertCircle className="w-4 h-4 text-red-500" />
          <span className="font-semibold">{errorText}</span>
        </div>
      )}

      {/* ── Floating Status Pill (Visualizer / Analyzing / Speaking) ── */}
      {(isRecording || isProcessing || isPlaying) && (
        <div className="bg-white/95 backdrop-blur-xl border border-emerald-100 px-4 py-2.5 rounded-full shadow-lg flex items-center justify-center gap-2 pointer-events-auto animate-fade-in mb-3">
          {isRecording ? (
            <div className="flex items-end gap-[3px] h-5 px-2">
              {visualizerBars.map((h, i) => (
                <div 
                  key={i} 
                  className="w-[2.5px] bg-emerald-500 rounded-full transition-all duration-75" 
                  style={{ height: `${h * 0.7}px` }} 
                />
              ))}
            </div>
          ) : isProcessing ? (
            <div className="flex items-center gap-1.5 text-[11px] font-bold text-gray-500">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-emerald-600" />
              <span>Analyzing...</span>
            </div>
          ) : isPlaying ? (
            <div className="flex items-center gap-1.5 text-[11px] font-bold text-emerald-600">
              <Volume2 className="w-3.5 h-3.5 animate-pulse" />
              <span>Speaking...</span>
            </div>
          ) : null}
        </div>
      )}

      {/* ── FAB Mic Trigger Button (Alone) ── */}
      <div className="pointer-events-auto relative flex items-center justify-center mb-1.5">
        <div className={`relative flex items-center justify-center ${!isRecording && !isProcessing && !isPlaying ? 'animate-pulse-ring' : ''}`}>
          <button
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isProcessing}
            className={`p-3.5 rounded-full text-white shadow-xl transition-all duration-300 hover:scale-105 active:scale-95 flex items-center justify-center relative z-10
              ${isRecording 
                ? 'bg-red-500 hover:bg-red-600 ring-4 ring-red-100 animate-pulse' 
                : (isPlaying || isProcessing || window.location.pathname === '/voice-consultant')
                  ? 'bg-emerald-700 hover:bg-emerald-800 ring-4 ring-emerald-250 scale-105'
                  : 'bg-emerald-600 hover:bg-emerald-700 ring-4 ring-emerald-100'}`}
          >
            {isRecording ? <Square className="w-5 h-5 fill-white" /> : <Mic className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* ── Hidden Audio Playback Element ── */}
      <audio 
        ref={audioPlayerRef} 
        onEnded={() => setIsPlaying(false)}
        className="hidden" 
      />

    </div>
  );
}
