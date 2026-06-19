import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, AlertCircle, Sparkles } from 'lucide-react';

export default function VoiceRecorder({ onRecordComplete, isProcessing }) {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState('');
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const animationFrameRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  
  // Waveform bars state for visualization
  const [waveHeights, setWaveHeights] = useState(new Array(15).fill(4));

  useEffect(() => {
    return () => {
      stopVisualizer();
    };
  }, []);

  const startVisualizer = (stream) => {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioContext();
      audioContextRef.current = audioCtx;
      
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const updateWave = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        
        // Take a slice of the frequency data and map to height values (4px to 50px)
        const newHeights = Array.from(dataArray.slice(0, 15)).map(val => 
          Math.max(4, (val / 255) * 50)
        );
        setWaveHeights(newHeights);
        animationFrameRef.current = requestAnimationFrame(updateWave);
      };

      updateWave();
    } catch (e) {
      console.error("Visualizer setup failed:", e);
    }
  };

  const stopVisualizer = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    analyserRef.current = null;
    setWaveHeights(new Array(15).fill(4));
  };

  const startRecording = async () => {
    setError('');
    audioChunksRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      
      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
          const base64Audio = reader.result.split(',')[1];
          if (onRecordComplete) {
            onRecordComplete(base64Audio);
          }
        };
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      startVisualizer(stream);
    } catch (err) {
      console.error("Mic access denied:", err);
      setError("Microphone access denied or unsupported.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      stopVisualizer();
    }
  };

  return (
    <div className="flex flex-col items-center gap-4 p-6 bg-white border border-[var(--line)] rounded-3xl shadow-md w-full">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs px-4 py-2 rounded-xl flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Waveform Visualizer */}
      <div className="flex items-end justify-center gap-1.5 h-16 w-full px-4">
        {waveHeights.map((h, i) => (
          <div
            key={i}
            className={`w-1 rounded-full transition-all duration-75 ${
              isRecording ? 'bg-[var(--brand-500)]' : 'bg-gray-200'
            }`}
            style={{ height: `${h}px` }}
          />
        ))}
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isProcessing}
          className={`p-4 rounded-full text-white shadow-xl transition-all duration-300 hover:scale-105 active:scale-95 flex items-center justify-center ${
            isRecording
              ? 'bg-red-500 hover:bg-red-600 ring-4 ring-red-100 animate-pulse'
              : 'bg-[var(--brand-600)] hover:bg-[var(--brand-700)] ring-4 ring-emerald-100'
          }`}
        >
          {isRecording ? <Square className="w-6 h-6 fill-white" /> : <Mic className="w-6 h-6" />}
        </button>

        {isProcessing && (
          <div className="flex items-center gap-2 text-xs font-bold text-gray-500 animate-pulse">
            <Sparkles className="w-4 h-4 text-[var(--brand-600)] animate-spin" />
            <span>Processing Voice...</span>
          </div>
        )}
      </div>
    </div>
  );
}