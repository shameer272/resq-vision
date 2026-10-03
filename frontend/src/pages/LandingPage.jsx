import React from "react";
import {
  ShieldAlert,
  ArrowRight,
  Sparkles,
  Layers,
  FileCheck,
  Globe,
  Radio,
  Cpu,
  Eye,
  CheckCircle,
  ExternalLink,
} from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export default function LandingPage({ setActiveTab, onOpenApiKeyModal, systemStatus }) {
  const { t } = useLanguage();

  const featureCards = [
    {
      icon: Eye,
      title: t("landing.feat_multimodal_title", "Multimodal Fusion"),
      color: "from-blue-600 to-cyan-600",
      description: t(
        "landing.feat_multimodal_desc",
        "Processes multiple scene photographs (up to 4 perspectives) combined with voice recordings, witness descriptions, and geographic context through Gemma 4."
      ),
    },
    {
      icon: FileCheck,
      title: t("landing.feat_evidence_title", "Evidence-Linked Auditing"),
      color: "from-emerald-600 to-teal-600",
      description: t(
        "landing.feat_evidence_desc",
        "Strictly segregates visual facts (OBSERVED), caller testimony (USER_REPORTED), and AI deductions (INFERRED) with auditable visual evidence links."
      ),
    },
    {
      icon: Layers,
      title: t("landing.feat_agentic_title", "Agentic Tool Calling"),
      color: "from-purple-600 to-indigo-600",
      description: t(
        "landing.feat_agentic_desc",
        "Autonomous multi-step tool execution: synthesizes international METHANE operational reports, first-responder triage checklists, and local RAG guidelines."
      ),
    },
    {
      icon: Globe,
      title: t("landing.feat_multilingual_title", "Multilingual Intelligence"),
      color: "from-amber-600 to-orange-600",
      description: t(
        "landing.feat_multilingual_desc",
        "Native translation into Telugu (తెలుగు) and Hindi (हिन्दी) specifically engineered to preserve epistemic uncertainty and emergency safety notices."
      ),
    },
  ];

  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 md:pt-20">
        <div className="mx-auto max-w-5xl text-center px-4">
          {/* Hackathon Badge */}
          <div className="inline-flex items-center space-x-2 rounded-full border border-red-800/80 bg-red-950/50 px-4 py-1.5 text-xs font-semibold text-red-300 mb-6 shadow-inner">
            <span className="flex h-2 w-2 rounded-full bg-red-500 animate-ping" />
            <span>{t("landing.badge", "Hacktoberfest Hack Day Hyderabad × NIAT • Challenge: Best Use of Gemma 4")}</span>
          </div>

          {/* Title */}
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-white mb-6">
            {t("landing.hero_title_1", "RESQ")}{" "}
            <span className="bg-gradient-to-r from-red-500 via-rose-500 to-amber-500 bg-clip-text text-transparent">
              {t("landing.hero_title_2", "VISION")}
            </span>
          </h1>

          {/* Tagline */}
          <p className="text-xl sm:text-2xl font-semibold text-slate-200 tracking-wide mb-4">
            {t("landing.hero_tagline", "\"See the situation. Understand the risk. Communicate the response.\"")}
          </p>

          {/* Subheading */}
          <p className="mx-auto max-w-2xl text-sm sm:text-base text-slate-400 mb-8 leading-relaxed">
            {t(
              "landing.hero_subheading",
              "A multimodal emergency situation intelligence platform powered by Gemma 4. Transforms fragmented scene images, voice calls, and bystander reports into structured, evidence-linked situational intelligence for faster, safer response decisions."
            )}
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={() => setActiveTab("analyze")}
              className="flex items-center space-x-2 rounded-xl bg-red-600 px-6 py-3.5 text-sm font-bold text-white transition-all hover:bg-red-500 hover:scale-105 shadow-lg shadow-red-950/60"
            >
              <span>{t("landing.btn_analyze", "Analyze an Incident")}</span>
              <ArrowRight className="h-4 w-4" />
            </button>

            <button
              onClick={() => setActiveTab("demo")}
              className="flex items-center space-x-2 rounded-xl border border-slate-700 bg-slate-900/80 px-6 py-3.5 text-sm font-semibold text-slate-200 transition-all hover:bg-slate-800 hover:border-slate-600"
            >
              <Sparkles className="h-4 w-4 text-amber-400" />
              <span>{t("landing.btn_demo", "Explore Preloaded Demos")}</span>
            </button>

            {!systemStatus?.gemini_api_key_configured && (
              <button
                onClick={onOpenApiKeyModal}
                className="flex items-center space-x-1.5 rounded-xl border border-blue-800/80 bg-blue-950/40 px-5 py-3.5 text-xs font-semibold text-blue-300 hover:bg-blue-900/50"
              >
                <span>{t("landing.btn_add_key", "Add Gemini Key for Live Gemma 4")}</span>
              </button>
            )}
          </div>
        </div>
      </section>

      {/* Feature Cards Grid */}
      <section className="mx-auto max-w-6xl px-4">
        <div className="text-center mb-10">
          <h2 className="text-2xl sm:text-3xl font-bold text-white">
            {t("landing.features_heading", "Architected for Operational Incident Clarity")}
          </h2>
          <p className="mt-2 text-xs sm:text-sm text-slate-400 max-w-xl mx-auto">
            {t(
              "landing.features_subheading",
              "Emergency responders face fragmented calls and conflicting reports. ResQ Vision synthesizes multimodal evidence while strictly upholding safety boundaries."
            )}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {featureCards.map((feat, idx) => {
            const Icon = feat.icon;
            return (
              <div
                key={idx}
                className="group relative rounded-2xl border border-slate-800 bg-slate-900/50 p-6 transition-all hover:border-slate-700 hover:bg-slate-900/90 shadow-md"
              >
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${feat.color} text-white mb-4 shadow-lg`}
                >
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{feat.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{feat.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Architecture & Multimodal Workflow Visual */}
      <section className="mx-auto max-w-5xl px-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 md:p-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 pb-6 border-b border-slate-800">
            <div>
              <div className="inline-flex items-center space-x-1.5 text-xs font-bold uppercase tracking-wider text-blue-400 mb-1">
                <Cpu className="h-4 w-4" />
                <span>{t("landing.pipeline_badge", "End-to-End Multimodal Pipeline")}</span>
              </div>
              <h3 className="text-xl font-bold text-white">{t("landing.pipeline_heading", "How Gemma 4 Operates in ResQ Vision")}</h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">
              Model: {systemStatus?.model || "gemma-4-31b-it"} via Google GenAI SDK
            </span>
          </div>

          {/* Workflow Diagram */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-center">
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                {t("landing.step1_badge", "Step 1: Ingestion")}
              </span>
              <div className="font-semibold text-sm text-slate-200">{t("landing.step1_title", "Scene Images + Voice + Text")}</div>
              <p className="mt-1 text-[11px] text-slate-400">
                {t("landing.step1_desc", "1-4 photographs with optional audio recording & location cues")}
              </p>
            </div>

            <div className="rounded-xl border border-blue-900/60 bg-blue-950/20 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400 block mb-1">
                {t("landing.step2_badge", "Step 2: Gemma 4")}
              </span>
              <div className="font-semibold text-sm text-blue-200">{t("landing.step2_title", "Multimodal Reasoning")}</div>
              <p className="mt-1 text-[11px] text-slate-400">
                {t("landing.step2_desc", "Cross-modal fusion with RAG safety knowledge base citations")}
              </p>
            </div>

            <div className="rounded-xl border border-amber-900/60 bg-amber-950/20 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 block mb-1">
                {t("landing.step3_badge", "Step 3: Provenance")}
              </span>
              <div className="font-semibold text-sm text-amber-200">{t("landing.step3_title", "Evidence Linkage")}</div>
              <p className="mt-1 text-[11px] text-slate-400">
                {t("landing.step3_desc", "Observed vs Reported vs Inferred with uncertainty calibration")}
              </p>
            </div>

            <div className="rounded-xl border border-emerald-900/60 bg-emerald-950/20 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 block mb-1">
                {t("landing.step4_badge", "Step 4: Agent Tools")}
              </span>
              <div className="font-semibold text-sm text-emerald-200">{t("landing.step4_title", "Actionable Output")}</div>
              <p className="mt-1 text-[11px] text-slate-400">
                {t("landing.step4_desc", "METHANE report, first-responder checklist, translation, & PDF export")}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Powered by Gemma 4 Banner */}
      <section className="mx-auto max-w-5xl px-4">
        <div className="rounded-2xl border border-blue-900/80 bg-gradient-to-r from-blue-950/60 via-slate-900/80 to-slate-950 p-6 md:p-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center space-x-2 text-xs font-bold text-blue-400">
                <Cpu className="h-4 w-4" />
                <span>{t("landing.banner_badge", "OFFICIAL CHALLENGE TRACK")}</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-extrabold text-white">
                {t("landing.banner_heading", "Powered by Google Gemma 4")}
              </h3>
              <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
                {t(
                  "landing.banner_desc",
                  "Gemma 4 performs multimodal analysis of incident images together with user-provided textual and voice context, produces structured situational observations, and participates in the tool-driven incident workflow via the Google GenAI SDK."
                )}
              </p>
            </div>

            <button
              onClick={() => setActiveTab("about")}
              className="shrink-0 flex items-center space-x-1.5 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-blue-500"
            >
              <span>{t("landing.btn_view_tech", "View Technical Details")}</span>
              <ExternalLink className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

