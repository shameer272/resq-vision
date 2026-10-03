import React from "react";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export default function Timeline({ events = [] }) {
  const { t } = useLanguage();

  if (!events || events.length === 0) return null;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
        {t("timeline.title", "Incident Timeline & Processing Pipeline")}
      </div>

      <div className="relative flex flex-col md:flex-row items-start md:items-center justify-between gap-2 overflow-x-auto pb-2 scrollbar-none">
        {events.map((evt, idx) => (
          <React.Fragment key={idx}>
            <div className="flex items-center space-x-2 shrink-0">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-950/80 border border-emerald-600 text-emerald-300">
                <CheckCircle2 className="h-3.5 w-3.5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-200">{evt.title}</div>
                <div className="text-[10px] text-slate-500 font-mono">{evt.timestamp}</div>
              </div>
            </div>

            {idx < events.length - 1 && (
              <div className="hidden md:flex items-center text-slate-600 shrink-0 px-1">
                <ArrowRight className="h-3.5 w-3.5" />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}
