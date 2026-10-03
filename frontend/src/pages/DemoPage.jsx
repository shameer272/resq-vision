import React, { useState, useEffect } from "react";
import {
  Sparkles,
  ArrowRight,
  Car,
  Droplets,
  Flame,
  AlertOctagon,
  CheckCircle,
  FileText,
  Languages,
  CheckSquare,
  ExternalLink,
} from "lucide-react";
import { getDemoScenarios } from "../services/api";
import { useLanguage } from "../context/LanguageContext";

export default function DemoPage({ setActiveTab, onSelectDemo }) {
  const { t } = useLanguage();
  const [demos, setDemos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDemoScenarios()
      .then((data) => setDemos(data))
      .catch((err) => console.error("Error loading demo scenarios:", err))
      .finally(() => setLoading(false));
  }, []);

  const getScenarioIcon = (id) => {
    switch (id) {
      case "DEMO-01":
        return Car;
      case "DEMO-02":
        return Droplets;
      case "DEMO-03":
        return Flame;
      case "DEMO-04":
      default:
        return AlertOctagon;
    }
  };

  const handleLaunchScenario = (scenario) => {
    onSelectDemo(scenario);
    setActiveTab("analyze");
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 space-y-8">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <div className="inline-flex items-center space-x-2 rounded-full border border-amber-800/80 bg-amber-950/50 px-3.5 py-1 text-xs font-semibold text-amber-300">
          <Sparkles className="h-3.5 w-3.5 text-amber-400" />
          <span>{t("demo.badge", "Interactive Hackathon Demonstrations")}</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white">
          {t("demo.title", "Preloaded Safe Emergency Scenarios")}
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
          {t("demo.subtitle", "Designed for hackathon judges and evaluators to test multimodal reasoning, evidence linkage, tool calling, and Telugu translation. Preloaded scenarios supply verified photographic inputs, and the AI response is synthesized live by Gemma 4.")}
        </p>
      </div>

      {/* Demo Cards Grid */}
      {loading ? (
        <div className="py-16 text-center text-slate-500 text-xs">
          {t("demo.loading", "Loading demo scenarios...")}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {demos.map((demo) => {
            const Icon = getScenarioIcon(demo.id);
            return (
              <div
                key={demo.id}
                className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 transition-all hover:border-red-500/60 hover:bg-slate-900/90 shadow-xl"
              >
                {/* Image preview banner */}
                <div className="relative aspect-16/9 w-full overflow-hidden bg-slate-950">
                  <img
                    src={demo.sample_image_url}
                    alt={demo.title}
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent" />
                  
                  {/* Demo Badge */}
                  <div className="absolute top-3 left-3">
                    <span className="rounded bg-amber-500 px-2.5 py-1 text-[10px] font-bold text-slate-950 shadow-md uppercase tracking-wider">
                      {demo.badge}
                    </span>
                  </div>

                  <div className="absolute bottom-3 left-4 right-4 flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-white font-bold text-base">
                      <Icon className="h-5 w-5 text-red-400" />
                      <span>{demo.title}</span>
                    </div>
                    <span className="rounded bg-slate-900/80 px-2 py-0.5 text-[10px] text-slate-300 font-mono border border-slate-800">
                      {demo.id}
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-5 space-y-3 flex-1 flex flex-col justify-between">
                  <div className="space-y-2 text-xs">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                        {t("demo.location_label", "Location / Context")}
                      </span>
                      <p className="font-semibold text-slate-200">{demo.location}</p>
                    </div>

                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                        {t("demo.witness_label", "Witness Description")}
                      </span>
                      <p className="text-slate-300 italic">"{demo.user_text}"</p>
                    </div>

                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                        {t("audio.transcript_label", "Voice Audio Transcript")}
                      </span>
                      <p className="text-slate-300 italic">"{demo.voice_transcript}"</p>
                    </div>
                  </div>

                  {/* Launch button */}
                  <div className="pt-4 border-t border-slate-800/80">
                    <button
                      onClick={() => handleLaunchScenario(demo)}
                      className="w-full flex items-center justify-center space-x-2 rounded-xl bg-slate-800 border border-slate-700 py-2.5 text-xs font-bold text-slate-200 hover:bg-red-600 hover:border-red-600 hover:text-white transition-all shadow-md group"
                    >
                      <span>{t("demo.btn_load", "Load into Gemma 4 Pipeline")}</span>
                      <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Suggested 3-Step Judge Walkthrough */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 md:p-8 space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
          Suggested Judge Walkthrough (End-to-End Workflow)
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
            <span className="text-red-400 font-bold block mb-1">1. Pick Demo Scenario</span>
            <p className="text-slate-400 text-[11px]">
              Click <strong>"Load into Gemma 4 Pipeline"</strong> on Scenario 1 (Road Accident).
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
            <span className="text-blue-400 font-bold block mb-1">2. Run Multimodal Analysis</span>
            <p className="text-slate-400 text-[11px]">
              Click <strong>"Analyze Incident"</strong> to watch Gemma 4 synthesize evidence-linked observations.
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
            <span className="text-amber-400 font-bold block mb-1">3. Translate & Checklist</span>
            <p className="text-slate-400 text-[11px]">
              Click <strong>"తెలుగు"</strong> to inspect preserved uncertainty, then trigger <strong>"Generate Checklist"</strong>.
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
            <span className="text-emerald-400 font-bold block mb-1">4. Export METHANE PDF</span>
            <p className="text-slate-400 text-[11px]">
              Generate the METHANE report and click <strong>"Download PDF"</strong> for official operational export.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
