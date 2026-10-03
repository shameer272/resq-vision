import React from "react";
import { Eye, User, Sparkles, CheckCircle2, AlertCircle } from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export default function ObservationCard({ observation }) {
  const { t } = useLanguage();
  const { description, source, confidence, evidence, source_label } = observation;

  const sourceConfig = {
    observed: {
      label: source_label || t("obs.observed", "Observed (Visual)"),
      icon: Eye,
      badgeClass: "bg-cyan-950/80 text-cyan-300 border-cyan-800/60",
      iconColor: "text-cyan-400",
    },
    user_reported: {
      label: source_label || t("obs.user_reported", "User Reported"),
      icon: User,
      badgeClass: "bg-purple-950/80 text-purple-300 border-purple-800/60",
      iconColor: "text-purple-400",
    },
    inferred: {
      label: source_label || t("obs.inferred", "Inferred (Requires Verification)"),
      icon: Sparkles,
      badgeClass: "bg-amber-950/80 text-amber-300 border-amber-800/60",
      iconColor: "text-amber-400",
    },
  };

  const currentSource = sourceConfig[source] || sourceConfig.inferred;
  const SourceIcon = currentSource.icon;

  const confidenceBadge = {
    high: "bg-emerald-950/60 text-emerald-400 border-emerald-800/50",
    medium: "bg-amber-950/60 text-amber-400 border-amber-800/50",
    low: "bg-slate-800 text-slate-400 border-slate-700",
  }[confidence] || "bg-slate-800 text-slate-400";

  const confidenceLabel = {
    high: t("obs.confidence_high", "High Confidence"),
    medium: t("obs.confidence_medium", "Medium Confidence"),
    low: t("obs.confidence_low", "Low Confidence"),
  }[confidence] || `${confidence} Confidence`;

  return (
    <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-900/60 p-4 transition-all hover:border-slate-700 hover:bg-slate-900/80 shadow-sm">
      {/* Header chips */}
      <div className="flex items-center justify-between gap-2 mb-2.5">
        <span
          className={`inline-flex items-center space-x-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${currentSource.badgeClass}`}
        >
          <SourceIcon className={`h-3 w-3 ${currentSource.iconColor}`} />
          <span>{currentSource.label}</span>
        </span>

        <span
          className={`rounded border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${confidenceBadge}`}
        >
          {confidenceLabel}
        </span>
      </div>

      {/* WHAT */}
      <div className="mb-2">
        <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400 mb-0.5">
          {t("obs.observation_label", "Observation")}
        </div>
        <p className="text-sm font-medium text-slate-100 leading-snug">{description}</p>
      </div>

      {/* EVIDENCE */}
      <div className="mt-auto pt-2.5 border-t border-slate-800/80">
        <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500 mb-0.5">
          {t("obs.evidence_label", "Auditable Evidence Base")}
        </div>
        <p className="text-xs text-slate-300 italic bg-slate-950/50 rounded p-2 border border-slate-900">
          "{evidence || t("obs.default_evidence", "Visible features from submitted scene imagery")}"
        </p>
      </div>
    </div>
  );
}
