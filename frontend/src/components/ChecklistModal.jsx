import React, { useState } from "react";
import { X, CheckSquare, Square, ShieldCheck, AlertCircle, Printer } from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export default function ChecklistModal({ isOpen, onClose, checklistData }) {
  const { t } = useLanguage();
  const [checkedItems, setCheckedItems] = useState({});

  if (!isOpen || !checklistData) return null;

  const toggleCheck = (id) => {
    setCheckedItems((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const items = checklistData.checklist_items || [];
  const cautions = checklistData.critical_cautions || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
      <div className="relative flex max-h-[90vh] w-full max-w-2xl flex-col rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <div className="flex items-center space-x-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
              <CheckSquare className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">
                {t("checklist.title", "Responder Information Verification Checklist")}
              </h3>
              <p className="text-xs text-slate-400">
                {t("checklist.subtitle", "Operational field verification protocol for on-scene first responders")}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto px-6 py-5 space-y-4 text-xs">
          {/* Cautions banner */}
          <div className="rounded-xl border border-amber-900/60 bg-amber-950/20 p-3 text-amber-200">
            <div className="flex items-center space-x-1.5 font-bold mb-1">
              <AlertCircle className="h-4 w-4 text-amber-400 shrink-0" />
              <span>{t("checklist.critical_directives", "Critical First-Responder Safety Directives:")}</span>
            </div>
            <ul className="list-disc list-inside space-y-0.5 text-slate-300">
              {cautions.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          </div>

          {/* Checklist Items */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
              {t("checklist.triage_items", "Triage Verification Items")} ({Object.values(checkedItems).filter(Boolean).length}/
              {items.length} {t("checklist.verified_suffix", "Verified")})
            </h4>
            {items.map((item) => {
              const isChecked = !!checkedItems[item.id];
              return (
                <div
                  key={item.id}
                  onClick={() => toggleCheck(item.id)}
                  className={`flex items-start space-x-3 rounded-lg border p-3 cursor-pointer transition-all ${
                    isChecked
                      ? "border-emerald-800/60 bg-emerald-950/20 text-slate-300"
                      : "border-slate-800 bg-slate-950/50 hover:border-slate-700 hover:bg-slate-950/80 text-slate-200"
                  }`}
                >
                  <div className="mt-0.5 shrink-0 text-emerald-400">
                    {isChecked ? (
                      <CheckSquare className="h-4 w-4 text-emerald-400" />
                    ) : (
                      <Square className="h-4 w-4 text-slate-500" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className={`font-semibold ${isChecked ? "line-through text-slate-400" : ""}`}>
                        {item.label}
                      </span>
                      <span
                        className={`text-[9px] uppercase px-1.5 py-0.5 rounded font-bold ${
                          item.priority === "critical"
                            ? "bg-red-950 text-red-400 border border-red-800/60"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {item.priority}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] text-slate-400 leading-relaxed">
                      {item.instruction}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-slate-800 px-6 py-3 bg-slate-950/60">
          <span className="text-[11px] text-slate-500">
            {checklistData.human_verification_notice}
          </span>
          <button
            onClick={onClose}
            className="rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500"
          >
            {t("checklist.btn_acknowledge", "Acknowledge & Close")}
          </button>
        </div>
      </div>
    </div>
  );
}
