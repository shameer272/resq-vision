import React, { useState } from "react";
import {
  ShieldAlert,
  Send,
  Loader2,
  FileCheck,
  CheckSquare,
  Volume2,
  VolumeX,
  Languages,
  Download,
  Save,
  AlertTriangle,
  Info,
  MapPin,
  Tag,
  BookOpen,
  HelpCircle,
  Sparkles,
} from "lucide-react";
import ImageUploader from "../components/ImageUploader";
import AudioRecorder from "../components/AudioRecorder";
import ObservationCard from "../components/ObservationCard";
import ConcernCard from "../components/ConcernCard";
import ActionTrace from "../components/ActionTrace";
import Timeline from "../components/Timeline";
import ReportModal from "../components/ReportModal";
import ChecklistModal from "../components/ChecklistModal";
import {
  analyzeIncident,
  analyzeMultiImage,
  generateReport,
  generateChecklist,
  translateIncident,
  exportPdf,
  saveIncidentEndpoint,
} from "../services/api";
import { useLanguage } from "../context/LanguageContext";

function stripLanguagePrefixes(str) {
  if (typeof str !== "string") return str;
  return str.replace(/^\s*(\[(?:Telugu|Hindi|English|te|hi|en)[^\]]*\]\s*)+/gi, "").trim();
}

function sanitizeIncidentData(obj) {
  if (!obj) return obj;
  if (typeof obj === "string") return stripLanguagePrefixes(obj);
  if (Array.isArray(obj)) return obj.map(sanitizeIncidentData);
  if (typeof obj === "object") {
    const clean = {};
    for (const [key, val] of Object.entries(obj)) {
      clean[key] = sanitizeIncidentData(val);
    }
    return clean;
  }
  return obj;
}

export default function AnalyzePage({
  selectedLanguage: propLanguage,
  setSelectedLanguage: propSetLanguage,
  systemStatus,
  preloadedScenario,
  onClearPreloaded,
  onOpenApiKeyModal,
}) {
  const { t, language, setLanguage } = useLanguage();
  const selectedLanguage = propLanguage || language;
  const setSelectedLanguage = (lang) => {
    if (propSetLanguage) propSetLanguage(lang);
    setLanguage(lang);
  };
  // Input states
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [userText, setUserText] = useState("");
  const [voiceTranscript, setVoiceTranscript] = useState("");
  const [location, setLocation] = useState("");
  const [category, setCategory] = useState("auto");

  // Pipeline states
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);

  // Canonical analysis result (English source of truth, never mutated on language switch)
  const [canonicalResult, setCanonicalResult] = useState(null);
  // Cache of translations: { en: canonicalResult, te: ..., hi: ... }
  const [translationsCache, setTranslationsCache] = useState({});

  const updateCanonicalResult = (raw) => {
    if (!raw) {
      setCanonicalResult(null);
      setTranslationsCache({});
      return;
    }
    const clean = sanitizeIncidentData(raw);
    setCanonicalResult(clean);
    setTranslationsCache({ en: clean });
  };

  // Derived displayed result: canonicalResult for English or cached translation for target language
  const displayedResult =
    (selectedLanguage === "en" ? canonicalResult : translationsCache[selectedLanguage]) ||
    canonicalResult;

  // Modals & Tools
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [isChecklistOpen, setIsChecklistOpen] = useState(false);
  const [checklistData, setChecklistData] = useState(null);

  // Tool loaders
  const [translating, setTranslating] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [generatingChecklist, setGeneratingChecklist] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // SpeechSynthesis voice output
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Auto-translate or switch translation when selectedLanguage changes or canonicalResult changes
  React.useEffect(() => {
    if (!canonicalResult) return;
    if (selectedLanguage === "en") return;
    if (translationsCache[selectedLanguage]) return;

    let isCancelled = false;
    const runTranslation = async () => {
      try {
        setTranslating(true);
        // CRITICAL: Always translate from canonicalResult, never from an already-translated object!
        const res = await translateIncident(canonicalResult, selectedLanguage);
        if (!isCancelled && res?.translated_content) {
          const clean = sanitizeIncidentData(res.translated_content);
          setTranslationsCache((prev) => ({
            ...prev,
            [selectedLanguage]: clean,
          }));
        }
      } catch (err) {
        console.error("Auto-translation failed:", err);
      } finally {
        if (!isCancelled) {
          setTranslating(false);
        }
      }
    };

    runTranslation();

    return () => {
      isCancelled = true;
    };
  }, [selectedLanguage, canonicalResult, translationsCache]);

  // Load preloaded demo scenario if passed
  React.useEffect(() => {
    if (preloadedScenario) {
      setUserText(preloadedScenario.user_text || "");
      setVoiceTranscript(preloadedScenario.voice_transcript || "");
      setLocation(preloadedScenario.location || "");
      setCategory(preloadedScenario.category ? preloadedScenario.category.toLowerCase().replace(/[^a-z]/g, "_") : "auto");

      // If preloaded scenario has analysis results, load into canonicalResult
      if (preloadedScenario.incident_summary && preloadedScenario.observations) {
        updateCanonicalResult(preloadedScenario);
      }

      // Load sample image
      if (preloadedScenario.sample_image_url) {
        fetch(preloadedScenario.sample_image_url)
          .then((res) => res.blob())
          .then((blob) => {
            const file = new File([blob], `${preloadedScenario.id}_sample.jpg`, { type: "image/jpeg" });
            setSelectedFiles([file]);
            setPreviews([
              {
                file,
                url: URL.createObjectURL(blob),
                name: `${preloadedScenario.title} (Demo)`,
                size: (blob.size / (1024 * 1024)).toFixed(2) + " MB",
              },
            ]);
          })
          .catch((err) => console.warn("Could not load demo image blob:", err));
      }
    }
  }, [preloadedScenario]);

  // Main Analysis Handler
  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (selectedFiles.length === 0) {
      setAnalysisError("Please upload or capture at least one emergency scene photograph.");
      return;
    }

    try {
      setIsAnalyzing(true);
      setAnalysisError(null);

      const formData = new FormData();
      if (userText) formData.append("user_text", userText);
      if (voiceTranscript) formData.append("voice_transcript", voiceTranscript);
      if (location) formData.append("location", location);
      if (category && category !== "auto") formData.append("category", category);
      formData.append("language", "en"); // Always generate canonical English result

      let result;
      if (selectedFiles.length === 1) {
        formData.append("image", selectedFiles[0]);
        result = await analyzeIncident(formData);
      } else {
        selectedFiles.forEach((file) => formData.append("images", file));
        result = await analyzeMultiImage(formData);
      }

      updateCanonicalResult(result);
    } catch (err) {
      console.error("[Analysis Error]", err);
      setAnalysisError(err.message || "Incident analysis failed.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Tool: Generate Report
  const handleGenerateReport = async () => {
    if (!displayedResult) return;
    try {
      setGeneratingReport(true);
      const rep = await generateReport(displayedResult);
      setReportData(rep);
      setIsReportOpen(true);
    } catch (err) {
      alert("Error generating report: " + err.message);
    } finally {
      setGeneratingReport(false);
    }
  };

  // Tool: Generate Checklist
  const handleGenerateChecklist = async () => {
    if (!displayedResult) return;
    try {
      setGeneratingChecklist(true);
      const chk = await generateChecklist(displayedResult);
      setChecklistData(chk);
      setIsChecklistOpen(true);
    } catch (err) {
      alert("Error generating checklist: " + err.message);
    } finally {
      setGeneratingChecklist(false);
    }
  };

  // Tool: Translate Report (switches global language and derives translation)
  const handleTranslate = (targetLang) => {
    setSelectedLanguage(targetLang);
  };

  // Tool: Download PDF
  const handleDownloadPdf = async () => {
    if (!displayedResult) return;
    try {
      setExportingPdf(true);
      await exportPdf(displayedResult);
    } catch (err) {
      alert("PDF download failed: " + err.message);
    } finally {
      setExportingPdf(false);
    }
  };

  // Tool: Read Aloud Voice Output
  const handleToggleSpeech = () => {
    if (!window.speechSynthesis) {
      alert("Browser speech synthesis is not supported on this device.");
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    if (!displayedResult) return;

    // Build concise, safety-checked verbal speech string
    const speechText = [
      `Emergency situation summary: ${displayedResult.incident_summary}.`,
      displayedResult.potential_concerns?.length
        ? `Identified potential concerns: ${displayedResult.potential_concerns.map((c) => c.concern).join(". ")}.`
        : "",
      "Human verification required by on-scene personnel.",
    ].join(" ");

    const utterance = new SpeechSynthesisUtterance(speechText);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
    setIsSpeaking(true);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 space-y-8">
      {/* Top Banner if API Key is missing */}
      {!systemStatus?.gemini_api_key_configured && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 rounded-xl border border-amber-800/80 bg-amber-950/40 p-4 text-xs text-amber-200">
          <div className="flex items-center space-x-2.5">
            <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
            <span>
              <strong>{t("analyze.api_key_required", "Gemini API Key Required:")}</strong>{" "}
              {t(
                "analyze.api_key_required_desc",
                "To run live multimodal inference with Gemma 4, please configure your server-side API key."
              )}
            </span>
          </div>
          <button
            onClick={onOpenApiKeyModal}
            className="shrink-0 rounded-lg bg-amber-500 px-3 py-1.5 font-bold text-slate-950 hover:bg-amber-400 transition-colors"
          >
            {t("analyze.btn_configure_key", "Configure Key")}
          </button>
        </div>
      )}

      {/* Preloaded Scenario Notice */}
      {preloadedScenario && (
        <div className="flex items-center justify-between rounded-xl border border-blue-800/80 bg-blue-950/40 p-3.5 text-xs text-blue-200">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-4 w-4 text-blue-400" />
            <span>
              {t("analyze.loaded_scenario", "Loaded")} <strong>{preloadedScenario.title}</strong> ({preloadedScenario.badge})
            </span>
          </div>
          <button
            onClick={onClearPreloaded}
            className="text-xs text-blue-400 hover:text-white underline"
          >
            {t("analyze.btn_reset_form", "Reset Form")}
          </button>
        </div>
      )}

      {/* Main Analysis Input Form */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Image & Voice (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Section A: Upload Incident */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-red-600/20 text-red-400 text-xs font-bold border border-red-500/40">
                  1
                </span>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  {t("analyze.section1_title", "Scene Photography (1–4 Views)")}
                </h3>
              </div>
              <span className="text-[11px] text-slate-400">{t("analyze.section1_limits", "JPEG • PNG • WebP (Max 10MB)")}</span>
            </div>
            <ImageUploader
              selectedFiles={selectedFiles}
              setSelectedFiles={setSelectedFiles}
              previews={previews}
              setPreviews={setPreviews}
            />
          </div>

          {/* Section B: Voice Input */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
            <div className="flex items-center space-x-2 mb-3">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-red-600/20 text-red-400 text-xs font-bold border border-red-500/40">
                2
              </span>
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                {t("analyze.section2_title", "Voice Input & Verbal Dispatch")}
              </h3>
            </div>
            <AudioRecorder
              transcript={voiceTranscript}
              setTranscript={setVoiceTranscript}
            />
          </div>
        </div>

        {/* Right Column: Text & Context (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg space-y-4">
            <div className="flex items-center space-x-2 mb-1">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-red-600/20 text-red-400 text-xs font-bold border border-red-500/40">
                3
              </span>
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                {t("analyze.section3_title", "Text Description & Context")}
              </h3>
            </div>

            {/* Section C: Text Description */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                {t("analyze.label_describe", "Describe what is happening...")}
              </label>
              <textarea
                rows={3}
                value={userText}
                onChange={(e) => setUserText(e.target.value)}
                placeholder={t("analyze.placeholder_describe", "E.g., Two sedans collided in middle lane. Grey smoke billowing from radiator, road blocked...")}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 p-3 text-xs text-slate-200 placeholder-slate-500 focus:border-red-500 focus:outline-none"
              />
            </div>

            {/* Section D: Optional Context */}
            <div className="space-y-3 pt-2 border-t border-slate-800/80">
              <div>
                <label className="flex items-center text-xs font-semibold text-slate-300 mb-1">
                  <MapPin className="h-3.5 w-3.5 mr-1 text-slate-400" />
                  <span>{t("analyze.label_location", "Reported Location / Landmark")}</span>
                </label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder={t("analyze.placeholder_location", "E.g., Gachibowli Junction, Hyderabad or NH 44")}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:border-red-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="flex items-center text-xs font-semibold text-slate-300 mb-1">
                    <Tag className="h-3.5 w-3.5 mr-1 text-slate-400" />
                    <span>{t("analyze.label_category", "Incident Category")}</span>
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-2.5 py-2 text-xs text-slate-200 focus:border-red-500 focus:outline-none"
                  >
                    <option value="auto">{t("analyze.cat_auto", "Auto Detect")}</option>
                    <option value="road_accident">{t("analyze.cat_road", "Road Accident")}</option>
                    <option value="smoke_fire">{t("analyze.cat_smoke", "Smoke / Fire")}</option>
                    <option value="flooding">{t("analyze.cat_flood", "Flooding / Water Hazard")}</option>
                    <option value="severe_weather">{t("analyze.cat_weather", "Severe Weather")}</option>
                    <option value="structural_damage">{t("analyze.cat_structure", "Damaged Building")}</option>
                    <option value="blocked_road">{t("analyze.cat_blocked", "Blocked Roadway")}</option>
                  </select>
                </div>

                <div>
                  <label className="flex items-center text-xs font-semibold text-slate-300 mb-1">
                    <Languages className="h-3.5 w-3.5 mr-1 text-slate-400" />
                    <span>{t("analyze.label_language", "Language")}</span>
                  </label>
                  <select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-2.5 py-2 text-xs text-slate-200 focus:border-red-500 focus:outline-none"
                  >
                    <option value="en">English</option>
                    <option value="te">తెలుగు (Telugu)</option>
                    <option value="hi">हिन्दी (Hindi)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Error Display */}
            {analysisError && (
              <div className="rounded-xl border border-red-900/80 bg-red-950/40 p-3 text-xs text-red-300">
                <div className="font-semibold flex items-center space-x-1.5 mb-1">
                  <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
                  <span>{t("analyze.analysis_notice", "Analysis Notice:")}</span>
                </div>
                <p className="leading-relaxed">{analysisError}</p>
                {analysisError.includes("API key") && (
                  <button
                    onClick={onOpenApiKeyModal}
                    className="mt-2 text-xs font-bold text-red-400 underline"
                  >
                    {t("analyze.click_api_key", "Click here to enter your Gemini API Key")}
                  </button>
                )}
              </div>
            )}

            {/* Section E: Analyze Button */}
            <div className="pt-2">
              <button
                type="button"
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="w-full flex items-center justify-center space-x-2 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 px-6 py-3.5 text-sm font-bold text-white shadow-lg shadow-red-950/60 hover:from-red-500 hover:to-rose-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>{t("analyze.btn_analyzing", "Analyzing with Gemma 4...")}</span>
                  </>
                ) : (
                  <>
                    <ShieldAlert className="h-4 w-4" />
                    <span>{t("analyze.btn_analyze", "Analyze Incident")}</span>
                  </>
                )}
              </button>
              <p className="mt-2 text-[10px] text-center text-slate-500">
                {t(
                  "analyze.notice_inference",
                  "Executes multimodal reasoning via Google GenAI SDK. Real inference latency applies."
                )}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================== */}
      {/* RESULTS DASHBOARD */}
      {/* ========================================================== */}
      {displayedResult && (
        <div className="space-y-6 pt-4 border-t border-slate-800">
          {/* Action Toolbar */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-slate-300">{t("analyze.tools_label", "Incident Tools:")}</span>
              <span className="text-[10px] font-mono text-slate-500">
                ID: {displayedResult.incident_id}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {/* Voice Read Aloud */}
              <button
                onClick={handleToggleSpeech}
                className={`flex items-center space-x-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-all ${
                  isSpeaking
                    ? "border-red-600 bg-red-950/60 text-red-300 animate-pulse"
                    : "border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700"
                }`}
              >
                {isSpeaking ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
                <span>{isSpeaking ? t("analyze.btn_stop_audio", "Stop Audio") : t("analyze.btn_read_aloud", "Read Aloud")}</span>
              </button>

              {/* Translate dropdown */}
              <div className="flex items-center rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1.5 text-xs font-medium text-slate-200">
                <Languages className={`h-3.5 w-3.5 mr-1.5 ${translating ? "animate-spin text-red-400" : "text-slate-400"}`} />
                <button
                  onClick={() => handleTranslate("te")}
                  disabled={translating}
                  className={`hover:text-red-400 pr-1.5 border-r border-slate-700 transition-colors ${selectedLanguage === "te" ? "text-red-400 font-bold" : ""}`}
                >
                  తెలుగు
                </button>
                <button
                  onClick={() => handleTranslate("hi")}
                  disabled={translating}
                  className={`hover:text-red-400 px-1.5 border-r border-slate-700 transition-colors ${selectedLanguage === "hi" ? "text-red-400 font-bold" : ""}`}
                >
                  हिन्दी
                </button>
                <button
                  onClick={() => handleTranslate("en")}
                  disabled={translating}
                  className={`hover:text-red-400 pl-1.5 transition-colors ${selectedLanguage === "en" ? "text-red-400 font-bold" : ""}`}
                >
                  EN
                </button>
              </div>

              {/* Responder Checklist */}
              <button
                onClick={handleGenerateChecklist}
                disabled={generatingChecklist}
                className="flex items-center space-x-1.5 rounded-lg border border-emerald-800/80 bg-emerald-950/40 px-3 py-1.5 text-xs font-medium text-emerald-300 hover:bg-emerald-900/50"
              >
                <CheckSquare className="h-3.5 w-3.5 text-emerald-400" />
                <span>
                  {generatingChecklist
                    ? t("analyze.btn_generating_checklist", "Generating...")
                    : t("analyze.btn_checklist", "Generate Checklist")}
                </span>
              </button>

              {/* METHANE Report */}
              <button
                onClick={handleGenerateReport}
                disabled={generatingReport}
                className="flex items-center space-x-1.5 rounded-lg border border-blue-800/80 bg-blue-950/40 px-3 py-1.5 text-xs font-medium text-blue-300 hover:bg-blue-900/50"
              >
                <FileCheck className="h-3.5 w-3.5 text-blue-400" />
                <span>
                  {generatingReport
                    ? t("analyze.btn_synthesizing_methane", "Synthesizing...")
                    : t("analyze.btn_methane", "METHANE Report")}
                </span>
              </button>

              {/* PDF Download */}
              <button
                onClick={handleDownloadPdf}
                disabled={exportingPdf}
                className="flex items-center space-x-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-500 shadow-md shadow-red-950/40"
              >
                <Download className="h-3.5 w-3.5" />
                <span>
                  {exportingPdf
                    ? t("analyze.btn_compiling_pdf", "Compiling...")
                    : t("analyze.btn_download_pdf", "Download PDF")}
                </span>
              </button>
            </div>
          </div>

          {/* Incident Summary Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded bg-red-950/80 border border-red-800/60 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider text-red-300">
                  {t(`types.${displayedResult.incident_type}`, displayedResult.incident_type?.replace(/_/g, " "))}
                </span>
                <div className="flex items-center space-x-1.5 text-xs text-slate-300 font-mono bg-slate-950/60 border border-slate-800 px-2.5 py-0.5 rounded">
                  <span className="text-slate-400">{t("analyze.analysis_engine", "Analysis Engine:")}</span>
                  <span className={displayedResult.fallback_used ? "text-amber-400 font-semibold" : "text-blue-400 font-semibold"}>
                    {displayedResult.model_used || "gemma-4-31b-it"}
                  </span>
                  {displayedResult.fallback_used ? (
                    <span 
                      className="ml-1 rounded bg-amber-950/90 border border-amber-700/80 px-1.5 py-0.2 text-[10px] text-amber-300 font-sans font-medium"
                      title={displayedResult.fallback_reason || "Switched to fallback model due to transient capacity error on primary model"}
                    >
                      ⚠️ {t("analyze.fallback_model", "Fallback")} (Primary: {displayedResult.primary_model || "gemma-4-31b-it"})
                    </span>
                  ) : (
                    <span className="ml-1 rounded bg-blue-950/80 border border-blue-700/60 px-1.5 py-0.2 text-[10px] text-blue-300 font-sans font-medium">
                      {t("analyze.primary_model", "Primary Model")}
                    </span>
                  )}
                </div>
              </div>
              <span className="rounded-full bg-emerald-950/60 border border-emerald-800/60 px-3 py-0.5 text-[11px] font-semibold text-emerald-300">
                {t("analyze.status_synthesized", "Status: Synthesized")}
              </span>
            </div>

            <h2 className="text-lg sm:text-xl font-bold text-white mb-2 leading-relaxed">
              {displayedResult.incident_summary}
            </h2>

            {/* Safety Disclaimer Banner */}
            <div className="mt-4 rounded-xl border border-red-900/60 bg-red-950/30 p-3 text-xs text-red-300 leading-relaxed">
              <strong>{t("analyze.mandatory_verification", "MANDATORY HUMAN VERIFICATION: ")}</strong>
              {displayedResult.safety_disclaimer}
            </div>
          </div>

          {/* Observations & Provenance Section */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                {t("analyze.heading_observations", "Evidence-Linked Observations (Data Provenance)")}
              </h3>
              <span className="text-xs text-slate-400">
                {displayedResult.observations?.length || 0} {t("analyze.points_identified", "Points Identified")}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {displayedResult.observations?.map((obs, idx) => (
                <ObservationCard key={idx} observation={obs} />
              ))}
            </div>
          </div>

          {/* Potential Concerns Section */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-amber-300">
                {t("analyze.heading_concerns", "Potential Safety Hazards & Concerns")}
              </h3>
              <span className="text-xs text-slate-400">
                {displayedResult.potential_concerns?.length || 0} {t("analyze.operational_hazards", "Operational Hazards")}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {displayedResult.potential_concerns?.map((c, idx) => (
                <ConcernCard key={idx} concernItem={c} />
              ))}
            </div>
          </div>

          {/* Two-column: Uncertainties + Missing Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Uncertainties */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-300 mb-3">
                <HelpCircle className="h-4 w-4 text-cyan-400" />
                <span>{t("analyze.heading_uncertainties", "Epistemic Uncertainties (Cannot Determine from Image)")}</span>
              </div>
              <ul className="space-y-1.5 text-xs text-slate-400 list-disc list-inside">
                {displayedResult.uncertainties?.map((u, i) => (
                  <li key={i}>{u}</li>
                ))}
              </ul>
            </div>

            {/* Missing Critical Info */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-300 mb-3">
                <Info className="h-4 w-4 text-amber-400" />
                <span>{t("analyze.heading_missing_info", "Information Gaps Needed for Dispatchers")}</span>
              </div>
              <ul className="space-y-1.5 text-xs text-slate-400 list-disc list-inside">
                {displayedResult.missing_information?.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* RAG Knowledge Base Citations */}
          {displayedResult.rag_sources?.length > 0 && (
            <div className="rounded-xl border border-blue-900/50 bg-blue-950/20 p-4">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-blue-300 mb-3">
                <BookOpen className="h-4 w-4 text-blue-400" />
                <span>{t("analyze.heading_rag_citations", "Curated RAG Knowledge Base Citations (Verified Safety Protocols)")}</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                {displayedResult.rag_sources.map((src, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-slate-800 bg-slate-950/60 p-3"
                  >
                    <span className="font-bold text-slate-200 block mb-0.5">{src.title}</span>
                    <span className="text-[10px] text-blue-400 font-semibold block mb-1">
                      {t("analyze.source_label", "Source:")} {src.source}
                    </span>
                    <p className="text-slate-400 text-[11px] leading-relaxed">
                      "{src.relevance_snippet}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Audit Trail & Processing Pipeline */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <ActionTrace steps={displayedResult.action_trace} />
            <Timeline events={displayedResult.timeline} />
          </div>
        </div>
      )}

      {/* Modals */}
      <ReportModal
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
        reportData={reportData}
        incidentData={displayedResult}
      />

      <ChecklistModal
        isOpen={isChecklistOpen}
        onClose={() => setIsChecklistOpen(false)}
        checklistData={checklistData}
      />
    </div>
  );
}
