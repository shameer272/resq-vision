import React from "react";
import {
  ShieldAlert,
  Cpu,
  Layers,
  ShieldCheck,
  FileText,
  AlertTriangle,
  Globe,
  ExternalLink,
  Code2,
} from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export default function AboutPage() {
  const { t } = useLanguage();

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 space-y-10 text-slate-300 text-xs sm:text-sm">
      {/* Title */}
      <div className="border-b border-slate-800 pb-6">
        <div className="inline-flex items-center space-x-2 rounded-full border border-red-800/80 bg-red-950/40 px-3 py-1 text-xs font-semibold text-red-300 mb-3">
          <ShieldAlert className="h-3.5 w-3.5" />
          <span>{t("about.badge", "Hackathon Submission Reference")}</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white">
          {t("about.title", "About ResQ Vision")}
        </h1>
        <p className="text-slate-400 mt-2">
          {t("about.tagline", "\"See the situation. Understand the risk. Communicate the response.\"")}
        </p>
      </div>

      {/* Problem & Solution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-3">
          <h3 className="text-base font-bold text-red-400">{t("about.problem_title", "The Problem")}</h3>
          <p className="leading-relaxed text-slate-300">
            {t("about.problem_desc1", "Emergency response units lose critical minutes deciphering fragmented bystander phone calls, ambiguous photos, and chaotic voice descriptions. Dispatches often arrive with insufficient gear, incorrect vehicle packages, or hazardous blindspots.")}
          </p>
          <p className="leading-relaxed text-slate-400 text-xs">
            {t("about.problem_desc2", "Generic AI systems hallucinate dangerous directives, fabricate certainty, or issue unvetted medical diagnoses that put lives at risk.")}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-3">
          <h3 className="text-base font-bold text-emerald-400">{t("about.solution_title", "The Solution")}</h3>
          <p className="leading-relaxed text-slate-300">
            {t("about.solution_desc1", "ResQ Vision applies Google's Gemma 4 to ingest multiple emergency scene photographs, voice transcripts, and bystander descriptions simultaneously.")}
          </p>
          <p className="leading-relaxed text-slate-400 text-xs">
            {t("about.solution_desc2", "It strictly segments visible facts (OBSERVED), caller testimony (USER_REPORTED), and deductions (INFERRED), links auditable evidence to every observation, and triggers agentic tools for standardized METHANE reporting.")}
          </p>
        </div>
      </div>

      {/* Why Gemma 4 */}
      <div className="rounded-2xl border border-blue-900/80 bg-blue-950/20 p-6 md:p-8 space-y-4">
        <div className="flex items-center space-x-2 text-blue-400 font-bold uppercase tracking-wider text-xs">
          <Cpu className="h-4 w-4" />
          <span>{t("about.why_gemma_badge", "Target Challenge: Best Use of Gemma 4")}</span>
        </div>
        <h2 className="text-xl font-bold text-white">{t("about.why_gemma_title", "Why Gemma 4 is Core to ResQ Vision")}</h2>
        <p className="leading-relaxed text-slate-200">
          {t("about.why_gemma_desc", "Gemma 4 is the foundation of ResQ Vision's multimodal reasoning layer. Accessed via the official google-genai Python SDK:")}
        </p>
        <ul className="list-disc list-inside space-y-2 text-slate-300 leading-relaxed text-xs sm:text-sm">
          <li>
            <strong>{t("about.gemma_point1_title", "Multimodal Vision-Language Reasoning:")}</strong> {t("about.gemma_point1_desc", "Gemma 4 simultaneously analyzes high-resolution imagery and complex natural language descriptions without losing visual spatial grounding.")}
          </li>
          <li>
            <strong>{t("about.gemma_point2_title", "Multi-Image Fusion:")}</strong> {t("about.gemma_point2_desc", "Integrates up to 4 scene perspectives (e.g. vehicle crush deformation, roadway debris, egress route, crowds) into a unified operational assessment.")}
          </li>
          <li>
            <strong>{t("about.gemma_point3_title", "Strict Structured JSON Generation:")}</strong> {t("about.gemma_point3_desc", "Produces typed JSON conforming to our strict Pydantic operational schemas with automated self-correction repair prompts.")}
          </li>
          <li>
            <strong>{t("about.gemma_point4_title", "Multilingual Capability:")}</strong> {t("about.gemma_point4_desc", "Translates operational intelligence into Telugu and Hindi while mathematically preserving epistemic uncertainty and safety disclaimers.")}
          </li>
        </ul>
      </div>

      {/* Architecture & Safety */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Architecture */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-3">
          <div className="flex items-center space-x-2 text-slate-200 font-bold text-sm">
            <Layers className="h-4 w-4 text-purple-400" />
            <span>{t("about.arch_title", "Architecture & Security")}</span>
          </div>
          <ul className="space-y-2 text-xs text-slate-400">
            <li>• <strong>Frontend:</strong> React + Vite + Tailwind CSS + Lucide Icons + Recharts</li>
            <li>• <strong>Backend:</strong> FastAPI + Python 3.12 + Pydantic v2 + ReportLab</li>
            <li>• <strong>AI Layer:</strong> Gemma 4 (31B-IT / 26B-A4B-IT) via Google GenAI SDK</li>
            <li>• <strong>RAG Engine:</strong> Local verified safety knowledge base (NHTSA, FEMA, NDMA, NOAA)</li>
            <li>• <strong>Zero Client Secret Exposure:</strong> Gemini API keys remain strictly server-side</li>
          </ul>
        </div>

        {/* Safety & Ethics */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-3">
          <div className="flex items-center space-x-2 text-slate-200 font-bold text-sm">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>{t("about.safety_title", "Safety & Ethical Guardrails")}</span>
          </div>
          <ul className="space-y-2 text-xs text-slate-400">
            <li>• <strong>No Autonomous Dispatch:</strong> {t("about.guardrail1", "Does not deploy emergency vehicles autonomously.")}</li>
            <li>• <strong>No Medical Diagnosis:</strong> {t("about.guardrail2", "Prohibits clinical assertions; requires certified triage.")}</li>
            <li>• <strong>Bystander Safety:</strong> {t("about.guardrail3", "Rewrites dangerous directives into safe perimeter stand-off advisories.")}</li>
            <li>• <strong>Mandatory Disclaimer:</strong> {t("about.guardrail4", "All outputs mandate on-scene human verification.")}</li>
          </ul>
        </div>
      </div>

      {/* Limitations & Future Scope */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
        <h3 className="text-base font-bold text-white">{t("about.limitations_title", "Operational Limitations & Future Scope")}</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-slate-400">
          <div>
            <span className="font-semibold text-amber-400 block mb-1">{t("about.limitations_subtitle", "Current Limitations:")}</span>
            <p>
              {t("about.limitations_desc", "Visual assessment is constrained by camera resolution, smoke occlusion, and night illumination. Geolocation uses user-provided text landmarks when GIS live feed is disconnected.")}
            </p>
          </div>
          <div>
            <span className="font-semibold text-blue-400 block mb-1">{t("about.future_subtitle", "Future Roadmap:")}</span>
            <p>
              {t("about.future_desc", "Direct CAD (Computer-Aided Dispatch) integration with emergency dispatch systems, drone live video stream ingest, thermal sensor fusion, and local on-device Gemma 4 edge execution.")}
            </p>
          </div>
        </div>
      </div>

      {/* Hackathon Submission Footer */}
      <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 text-center text-xs text-slate-500">
        <p className="font-semibold text-slate-400">
          Hacktoberfest Hack Day Hyderabad × NIAT • ResQ Vision Team
        </p>
        <p className="mt-1">
          Open-Source Project licensed under Apache 2.0 • Google Gemma 4 Integration
        </p>
      </div>
    </div>
  );
}
