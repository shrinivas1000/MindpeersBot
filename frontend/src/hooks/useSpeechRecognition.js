/**
 * useSpeechRecognition — custom hook wrapping the browser Web Speech API.
 *
 * Provides speech-to-text capability using SpeechRecognition / webkitSpeechRecognition.
 * Returns isSupported=false in unsupported browsers (Firefox, Safari) so the
 * mic button can be hidden entirely.
 *
 * Features:
 * - Continuous mode: keeps listening across natural pauses in speech
 * - Real-time interim results for live typing feedback
 * - 5-second silence timeout: auto-stops if no speech detected for 5s
 * - 60-second max duration: hard cutoff to prevent runaway sessions
 * - Accumulated transcripts: multiple final segments are concatenated
 *
 * Usage:
 *   const { isSupported, isListening, error, finalText, interimText, startListening, stopListening }
 *     = useSpeechRecognition();
 */

import { useState, useRef, useCallback, useEffect } from 'react';

const SpeechRecognition =
  typeof window !== 'undefined'
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null;

const SILENCE_TIMEOUT_MS = 3000;  // Stop after 3s of no speech
const MAX_DURATION_MS = 60000;    // Hard cutoff at 60s

export default function useSpeechRecognition() {
  const [isListening, setIsListening] = useState(false);
  // Accumulated final transcript segments from the current listening session
  const [finalText, setFinalText] = useState('');
  // Current interim (unconfirmed) text
  const [interimText, setInterimText] = useState('');
  const [error, setError] = useState(null);

  const recognitionRef = useRef(null);
  const silenceTimerRef = useRef(null);
  const maxDurationTimerRef = useRef(null);
  const errorTimerRef = useRef(null);

  const isSupported = !!SpeechRecognition;

  // Clear error after 3 seconds
  useEffect(() => {
    if (error) {
      errorTimerRef.current = setTimeout(() => {
        setError(null);
      }, 3000);
      return () => clearTimeout(errorTimerRef.current);
    }
  }, [error]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      clearTimeout(silenceTimerRef.current);
      clearTimeout(maxDurationTimerRef.current);
      clearTimeout(errorTimerRef.current);
    };
  }, []);

  const clearTimers = useCallback(() => {
    clearTimeout(silenceTimerRef.current);
    clearTimeout(maxDurationTimerRef.current);
    silenceTimerRef.current = null;
    maxDurationTimerRef.current = null;
  }, []);

  const stopListening = useCallback(() => {
    clearTimers();
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  }, [clearTimers]);

  const resetSilenceTimer = useCallback(() => {
    clearTimeout(silenceTimerRef.current);
    silenceTimerRef.current = setTimeout(() => {
      // No speech for 5 seconds — auto-stop
      stopListening();
    }, SILENCE_TIMEOUT_MS);
  }, [stopListening]);

  const startListening = useCallback(() => {
    if (!isSupported || isListening) return;

    setError(null);
    setFinalText('');
    setInterimText('');

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);

      // Start the silence timer — will be reset on every result
      resetSilenceTimer();

      // Hard cutoff at 60 seconds
      maxDurationTimerRef.current = setTimeout(() => {
        stopListening();
      }, MAX_DURATION_MS);
    };

    recognition.onresult = (event) => {
      // Reset the silence timer on every result event
      resetSilenceTimer();

      // Rebuild the full accumulated final + current interim from all results
      let accumulated = '';
      let currentInterim = '';

      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          accumulated += result[0].transcript;
        } else {
          currentInterim += result[0].transcript;
        }
      }

      setFinalText(accumulated);
      setInterimText(currentInterim);
    };

    recognition.onerror = (event) => {
      const errorMessages = {
        'not-allowed': 'Microphone access was denied. Please allow mic permissions.',
        'no-speech': null, // In continuous mode, no-speech is normal during pauses
        'audio-capture': 'No microphone found. Please check your device.',
        'network': 'Network error occurred. Please check your connection.',
        'aborted': null, // User-initiated stop, not an error
      };

      const message = errorMessages[event.error] || `Speech recognition error: ${event.error}`;
      if (message) {
        setError(message);
        clearTimers();
        setIsListening(false);
      }
    };

    recognition.onend = () => {
      clearTimers();
      setIsListening(false);
      setInterimText('');
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [isSupported, isListening, resetSilenceTimer, stopListening, clearTimers]);

  return {
    isSupported,
    isListening,
    finalText,
    interimText,
    error,
    startListening,
    stopListening,
  };
}
