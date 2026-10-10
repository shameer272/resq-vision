import React, { useState, useRef, useEffect } from "react";
import { Mic, Square, Play, Pause, Trash2, Edit3, Check, AlertCircle } from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export default function AudioRecorder({ transcript, setTranscript, onAudioReady }) {
  const { t } = useLanguage();
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [speechApiSupported, setSpeechApiSupported] = useState(true);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const timerRef = useRef(null);
  const audioElementRef = useRef(null);

  useEffect(() => {
    // Check SpeechRecognition support
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onresult = (event) => {
        let currentTranscript = "";
        for (let i = 0; i < event.results.length; i++) {
          currentTranscript += event.results[i][0].transcript + " ";
        }
        setTranscript(currentTranscript.trim());
      };

      recognition.onerror = (event) => {
        console.warn("[Voice] Speech recognition error:", event.error);
      };

      recognitionRef.current = recognition;
    } else {
      setSpeechApiSupported(false);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [setTranscript]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);
        if (onAudioReady) onAudioReady(audioBlob);
        stream.getTracks().forEach((t) => t.stop());
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingSeconds(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);

      // Start speech recognition if supported
      if (recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch (e) {
          console.warn("Speech recognition already running or error:", e);
        }
      }
    } catch (err) {
      console.error("Microphone access error:", err);
      alert(
        t(
          "audio.err_mic",
          "Microphone access was denied or is unavailable. You can use the manual transcript editing box below."
        )
      );
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (_e) {
        // ignore
      }
    }
  };

  const togglePlayback = () => {
    if (!audioElementRef.current) return;
    if (isPlaying) {
      audioElementRef.current.pause();
      setIsPlaying(false);
    } else {
      audioElementRef.current.play();
      setIsPlaying(true);
    }
  };

  const clearAudio = () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setIsPlaying(false);
    setRecordingSeconds(0);
    setTranscript("");
  };

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const remain = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${remain.toString().padStart(2, "0")}`;
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Mic className="h-4 w-4 text-red-400" />
          <span className="text-sm font-semibold text-slate-200">
            {t("audio.title", "Voice Input & Dispatch Audio")}
          </span>
        </div>
        {!speechApiSupported && (
          <span className="flex items-center text-[11px] text-amber-400">
            <AlertCircle className="h-3 w-3 mr-1" /> {t("audio.fallback_notice", "Speech API Fallback")}
          </span>
        )}
      </div>

      {/* Recording Controls */}
      <div className="flex flex-wrap items-center gap-3">
        {!isRecording ? (
          <button
            type="button"
            onClick={startRecording}
            className="flex items-center space-x-2 rounded-lg bg-red-600 px-4 py-2 text-xs font-semibold text-white transition-all hover:bg-red-500 shadow-md shadow-red-950/40"
          >
            <Mic className="h-4 w-4" />
            <span>{t("audio.btn_record", "Record Voice")}</span>
          </button>
        ) : (
          <button
            type="button"
            onClick={stopRecording}
            className="flex items-center space-x-2 rounded-lg bg-slate-800 border border-red-500 px-4 py-2 text-xs font-semibold text-red-300 animate-pulse hover:bg-slate-700"
          >
            <Square className="h-4 w-4 text-red-400" />
            <span>{t("audio.btn_stop", "Stop")} ({formatTime(recordingSeconds)})</span>
          </button>
        )}

        {audioUrl && (
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={togglePlayback}
              className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-medium text-slate-200 hover:bg-slate-700"
            >
              {isPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
              <span>{isPlaying ? t("audio.btn_pause", "Pause") : t("audio.btn_play", "Play")}</span>
            </button>
            <button
              type="button"
              onClick={clearAudio}
              className="rounded-lg border border-slate-800 p-2 text-slate-400 hover:bg-slate-800 hover:text-red-400"
              title={t("audio.clear_title", "Clear voice recording")}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
            <audio
              ref={audioElementRef}
              src={audioUrl}
              onEnded={() => setIsPlaying(false)}
              className="hidden"
            />
          </div>
        )}
      </div>

      {/* Transcription Area */}
      <div className="mt-3">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
          <span>{t("audio.transcript_label", "Transcript (Gemma 4 Multimodal Voice Context)")}</span>
          <button
            type="button"
            onClick={() => setIsEditing(!isEditing)}
            className="flex items-center space-x-1 text-slate-400 hover:text-slate-200"
          >
            {isEditing ? <Check className="h-3 w-3 text-emerald-400" /> : <Edit3 className="h-3 w-3" />}
            <span>{isEditing ? t("audio.btn_done", "Done Editing") : t("audio.btn_edit", "Edit Text")}</span>
          </button>
        </div>

        {isEditing ? (
          <textarea
            rows={2}
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder={t("audio.placeholder_edit", "Edit voice transcript or type manual emergency report...")}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2.5 text-xs text-slate-200 placeholder-slate-500 focus:border-red-500 focus:outline-none"
          />
        ) : (
          <div className="min-h-[44px] rounded-lg border border-slate-800/80 bg-slate-950/60 p-2.5 text-xs text-slate-300">
            {transcript ? (
              <span className="italic">"{transcript}"</span>
            ) : (
              <span className="text-slate-600">
                {isRecording
                  ? t("audio.placeholder_listening", "Listening to voice input... speak clearly about the scene.")
                  : t("audio.placeholder_empty", "No voice recorded. Click 'Record Voice' or use text description.")}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

