import React, { useEffect, useRef, useState } from 'react';
import { Play, Pause, RotateCcw, Volume2 } from 'lucide-react';

export default function AudioPlayer({ audioBase64, audioFormat = 'audio/wav', onPlayStateChange }) {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1.0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (audioBase64 && audioRef.current) {
      audioRef.current.load();
      audioRef.current.playbackRate = speed;
      audioRef.current.play().catch(err => {
        console.error('Audio auto-play failed:', err);
        setIsPlaying(false);
      });
      setIsPlaying(true);
    }
  }, [audioBase64]);

  useEffect(() => {
    if (onPlayStateChange) onPlayStateChange(isPlaying);
  }, [isPlaying]);

  const handlePlayPause = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().catch(console.error);
      setIsPlaying(true);
    }
  };

  const handleRestart = () => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = 0;
    audioRef.current.play().catch(console.error);
    setIsPlaying(true);
  };

  const handleSpeedChange = (e) => {
    const rate = parseFloat(e.target.value);
    setSpeed(rate);
    if (audioRef.current) audioRef.current.playbackRate = rate;
  };

  const handleTimeUpdate = () => {
    if (!audioRef.current) return;
    const { currentTime, duration } = audioRef.current;
    setProgress(duration ? (currentTime / duration) * 100 : 0);
  };

  const handleAudioEnded = () => {
    setIsPlaying(false);
    setProgress(0);
  };

  if (!audioBase64) return null;

  return (
    <div className="flex flex-col gap-2 p-3 bg-[var(--brand-50)] border border-[var(--brand-200)] rounded-xl">
      <div className="flex items-center gap-2">
        <Volume2 className="w-4 h-4 text-[var(--brand-600)] flex-shrink-0" />
        <span className="text-xs font-bold text-[var(--brand-700)] flex-1">Krishi Audio Response</span>
        <select
          value={speed}
          onChange={handleSpeedChange}
          className="text-[10px] font-bold bg-white border border-[var(--brand-200)] rounded-lg px-1.5 py-0.5 text-[var(--brand-700)] outline-none cursor-pointer"
        >
          <option value={0.75}>0.75×</option>
          <option value={1.0}>1×</option>
          <option value={1.25}>1.25×</option>
          <option value={1.5}>1.5×</option>
        </select>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1.5 bg-[var(--brand-100)] rounded-full overflow-hidden">
        <div
          className="h-full bg-[var(--brand-500)] rounded-full transition-all duration-200"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={handlePlayPause}
          className="flex items-center justify-center w-8 h-8 rounded-full bg-[var(--brand-600)] text-white hover:bg-[var(--brand-700)] transition-colors shadow-sm"
        >
          {isPlaying ? <Pause className="w-4 h-4 fill-white" /> : <Play className="w-4 h-4 fill-white" />}
        </button>
        <button
          onClick={handleRestart}
          className="flex items-center justify-center w-7 h-7 rounded-full bg-white border border-[var(--brand-200)] text-[var(--brand-600)] hover:bg-[var(--brand-50)] transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
        <span className="text-[10px] text-gray-400 font-medium ml-auto">
          {isPlaying ? 'Playing...' : 'Paused'}
        </span>
      </div>

      <audio
        ref={audioRef}
        src={audioBase64 ? `data:${audioFormat};base64,${audioBase64}` : ''}
        onTimeUpdate={handleTimeUpdate}
        onEnded={handleAudioEnded}
        className="hidden"
      />
    </div>
  );
}