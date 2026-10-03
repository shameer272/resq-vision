import React from "react";
import { AlertTriangle, ShieldCheck, Flame, Zap, Droplets, Construction } from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export default function ConcernCard({ concernItem }) {
  const { t } = useLanguage();
  const { concern, reason, evidence, confidence, requires_human_verification, verification_label } =
    concernItem;

  const isHighPriority = confidence === "high";

  return (
    <div
      className={`rounded-xl border p-4 transition-all ${
        isHighPriority
          ? "border-red-900/60 bg-red-950/20 hover:border-red-800/80 hover:bg-red-950/30"
          : "border-amber-900/60 bg-amber-950/20 hover:border-amber-800/80 hover:bg-amber-950/30"
      }`}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center space-x-2">
          <div
            className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${
              isHighPriority
                ? "bg-red-900/50 text-red-400 border border-red-700/60"
                : "bg-amber-900/50 text-amber-400 border border-amber-700/60"
            }`}
          >
            <AlertTriangle className="h-4 w-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">{concern}</h4>
            <span className="text-[10px] text-slate-400 font-medium">
              {t("concern.priority_cue", "Priority Cue:")} <span className="uppercase">{confidence}</span> {t("concern.confidence_suffix", "confidence")}
            </span>
          </div>
        </div>

        {/* Human Verification Badge */}
        {requires_human_verification && (
          <span className="shrink-0 inline-flex items-center space-x-1 rounded-full border border-amber-700/60 bg-amber-950/80 px-2 py-0.5 text-[10px] font-semibold text-amber-300">
            <ShieldCheck className="h-3 w-3 text-amber-400" />
            <span>{verification_label || t("concern.verification_required", "Human Verification Required")}</span>
          </span>
        )}
      </div>

      {/* Reason */}
      <div className="mt-2 text-xs text-slate-300 leading-relaxed">
        <span className="font-semibold text-slate-400">{t("concern.risk_mechanism", "Risk Mechanism:")} </span>
        {reason}
      </div>

      {/* Observable Evidence */}
      <div className="mt-2.5 rounded-lg border border-slate-800/80 bg-slate-950/60 p-2 text-xs text-slate-300">
        <span className="text-[10px] uppercase font-bold text-slate-500 block mb-0.5">
          {t("concern.observable_evidence", "Observable Evidence:")}
        </span>
        <span className="italic">"{evidence}"</span>
      </div>
    </div>
  );
}
