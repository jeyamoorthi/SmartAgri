import { useState, useRef, useCallback } from 'react';
import API from '../api/axios';

/**
 * Custom hook for voice input using MediaRecorder + farm_advisory backend.
 * Records audio from browser mic → sends base64 to /api/advisory/voice-chat → returns transcription.
 */
export default function useVoiceInput() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState('');
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = useCallback(async () => {
    setError('');
    setTranscript('');
    chunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      setError('Microphone access denied. Please allow mic permissions.');
      console.error('Mic error:', err);
    }
  }, []);

  const stopRecording = useCallback(() => {
    return new Promise((resolve) => {
      const mediaRecorder = mediaRecorderRef.current;
      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        resolve('');
        return;
      }

      mediaRecorder.onstop = async () => {
        setIsRecording(false);
        setIsProcessing(true);

        try {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' });

          // Convert blob to base64
          const reader = new FileReader();
          const base64Promise = new Promise((res) => {
            reader.onloadend = () => {
              const base64 = reader.result.split(',')[1];
              res(base64);
            };
          });
          reader.readAsDataURL(blob);
          const audioBase64 = await base64Promise;
          
          resolve(audioBase64);
        } catch (err) {
          setError('Failed to process audio');
          resolve('');
        } finally {
          setIsProcessing(false);
          // Stop all tracks
          mediaRecorder.stream.getTracks().forEach((t) => t.stop());
        }
      };

      mediaRecorder.stop();
    });
  }, []);

  const reset = useCallback(() => {
    setTranscript('');
    setError('');
    setIsRecording(false);
    setIsProcessing(false);
  }, []);

  return {
    isRecording,
    isProcessing,
    transcript,
    error,
    startRecording,
    stopRecording,
    reset,
  };
}
