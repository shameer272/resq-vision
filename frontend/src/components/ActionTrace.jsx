import React from "react";
import { CheckCircle2, AlertCircle, Clock, ShieldCheck } from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export default function ActionTrace({ steps = [] }) {
  const { t } = useLanguage();

  if (!steps || steps.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex items-center justify-between mb-3 border-b border-slate-800/80 pb-2.5">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            {t("trace.title", "AI Action Trace & Audit Trail")}
          </h3>
        </div>
        <span className="text-[11px] text-slate-500 font-mono">
          {steps.length} {t("trace.steps_verified", "Steps Verified")}
        </span>
      </div>

      <div className="space-y-2">
        {steps.map((item, idx) => {
          const isFailed = item.status === "failed";
          return (
            <div
              key={idx}
              className="flex items-start justify-between rounded-lg border border-slate-800/60 bg-slate-950/40 px-3 py-2 text-xs"
            >
              <div className="flex items-start space-x-2.5">
                {isFailed ? (
                  <AlertCircle className="h-3.5 w-3.5 mt-0.5 text-red-400 shrink-0" />
                ) : (
                  <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 text-emerald-400 shrink-0" />
                )}
                <div>
                  <span className="font-semibold text-slate-200">{item.step}</span>
                  <p className="text-slate-400 text-[11px] mt-0.5">{item.description}</p>
                  {item.details && (
                    <p className="text-slate-500 text-[10px] mt-0.5 font-mono italic">
                      ↳ {item.details}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center space-x-1 text-[10px] text-slate-500 shrink-0 pl-2 font-mono">
                <Clock className="h-3 w-3" />
                <span>{item.timestamp}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
