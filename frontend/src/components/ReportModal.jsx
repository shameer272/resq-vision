import React, { useState } from "react";
import { X, Download, FileText, Printer, Check, Copy, Loader2 } from "lucide-react";
import { exportPdf } from "../services/api";
import { useLanguage } from "../context/LanguageContext";

export default function ReportModal({ isOpen, onClose, reportData, incidentData, loading = false }) {
  const { t } = useLanguage();
  const [downloading, setDownloading] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!isOpen || (!reportData && !incidentData && !loading)) return null;

  // Prefer reportData, fall back to incidentData
  const active = reportData || incidentData || {};

  const reportId = active.report_id || (active.incident_id ? `REP-${active.incident_id}` : "REP-RESQ-OPERATIONAL");
  const rawTimestamp = active.generated_at || active.timestamp || active.saved_at;
  const generatedAt = rawTimestamp 
    ? (rawTimestamp.includes("UTC") ? rawTimestamp : new Date(rawTimestamp).toLocaleString() + " UTC")
    : new Date().toUTCString();
  const executiveSummary = active.executive_summary || active.incident_summary || "Operational incident assessment compiled.";
  const safetyDisclaimer = active.ai_limitations_and_disclaimer || active.safety_disclaimer || (
    "LEGAL & SAFETY NOTICE: This report was synthesized using multimodal reasoning by Gemma 4. " +
    "It serves strictly as situational decision support for human responders. It does NOT constitute medical diagnosis, " +
    "does NOT autonomously dispatch assets, and DOES NOT supersede official emergency communications."
  );
  const observedFacts = active.observed_facts || active.observations || [];
  const potentialHazards = active.potential_hazards || active.potential_concerns || [];

  const defaultMethane = {
    "M - Major Incident Standby": (
      "STANDBY / SITUATIONAL INTELLIGENCE. Field evidence indicates active hazard dynamics; " +
      "on-scene incident commander must verify scale before full declaration."
    ),
    "E - Exact Location": active.location || "Unspecified location (Scene imagery provided)",
    "T - Type of Incident": (active.incident_type || "Incident").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    "H - Hazards Present / Suspected": (potentialHazards.map((c) => c.concern || c.reason || c).filter(Boolean).join("; ")) || "None clearly observable.",
    "A - Access and Egress": "Assess road blockages and emergency vehicle corridors. Advise units to approach from upwind/uphill.",
    "N - Number & Severity of Casualties": "Unconfirmed from imagery alone. On-scene responder triage required. Do not rely on AI for vital signs.",
    "E - Emergency Services Required": "Recommended triage package: Police/Traffic control, Fire & Rescue standby, EMS evaluation based on verification."
  };

  const methane = (active.methane_structure && Object.keys(active.methane_structure).length > 0)
    ? active.methane_structure
    : defaultMethane;

  const handleDownloadPdf = async () => {
    try {
      setDownloading(true);
      const pdfPayload = {
        ...active,
        report_id: reportId,
        incident_id: active.incident_id || (reportId ? reportId.replace("REP-", "") : "INCIDENT"),
        generated_at: generatedAt,
        executive_summary: executiveSummary,
        methane_structure: methane,
        observed_facts: observedFacts,
        potential_hazards: potentialHazards,
        ai_limitations_and_disclaimer: safetyDisclaimer,
      };
      await exportPdf(pdfPayload);
    } catch (e) {
      alert("Error compiling PDF: " + e.message);
    } finally {
      setDownloading(false);
    }
  };

  const handleCopyText = () => {
    const text = JSON.stringify(reportData || active, null, 2);
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
      <div className="relative flex max-h-[90vh] w-full max-w-4xl flex-col rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <div className="flex items-center space-x-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-950/80 text-red-400 border border-red-800/60">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">
                {t("report.title", "METHANE Operational Incident Report")}
              </h3>
              <p className="text-xs text-slate-400">
                {reportId} • Generated: {generatedAt}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopyText}
              className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              <span>{copied ? t("report.btn_copied", "Copied") : t("report.btn_copy", "Copy")}</span>
            </button>
            <button
              onClick={handleDownloadPdf}
              disabled={downloading}
              className="flex items-center space-x-1.5 rounded-lg bg-red-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-red-500 shadow-md shadow-red-950/40"
            >
              <Download className="h-3.5 w-3.5" />
              <span>{downloading ? t("report.btn_generating", "Generating...") : t("report.btn_download", "Download PDF")}</span>
            </button>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Body content */}
        <div className="overflow-y-auto px-6 py-5 space-y-5 text-slate-200 text-xs">
          {loading && (
            <div className="flex items-center space-x-2 rounded-xl border border-blue-900/60 bg-blue-950/30 p-3 text-blue-300">
              <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
              <span>{t("report.synthesizing_notice", "Synthesizing official METHANE Operational Report from stored incident intelligence...")}</span>
            </div>
          )}

          {/* Executive Summary */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
              {t("report.executive_summary", "Executive Situation Summary")}
            </h4>
            <p className="text-sm font-medium text-slate-100 leading-relaxed">
              {executiveSummary}
            </p>
          </div>

          {/* METHANE Matrix */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              {t("report.methane_breakdown", "METHANE Protocol Breakdown")}
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(methane).map(([k, v]) => (
                <div
                  key={k}
                  className="rounded-lg border border-slate-800/80 bg-slate-950/40 p-3"
                >
                  <span className="font-bold text-red-400 block mb-1">{k}</span>
                  <p className="text-slate-300 leading-relaxed">{v}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Observations & Provenance */}
          {observedFacts && observedFacts.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                {t("report.heading_observations", "Evidence-Linked Observations (Visual & Reported)")}
              </h4>
              <div className="space-y-2">
                {observedFacts.map((o, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col sm:flex-row sm:items-center justify-between rounded-lg border border-slate-800/60 bg-slate-950/40 p-2.5 gap-2"
                  >
                    <div>
                      <span className="font-semibold text-slate-200">{o.description}</span>
                      {o.evidence && (
                        <p className="text-[11px] text-slate-400 italic mt-0.5">
                          {t("report.evidence_prefix", "Evidence:")} "{o.evidence}"
                        </p>
                      )}
                    </div>
                    <span className="shrink-0 self-start sm:self-auto rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-cyan-300 uppercase">
                      {o.source || "observed"} • {o.confidence || "verified"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Potential Concerns */}
          {potentialHazards && potentialHazards.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 mb-2">
                {t("report.heading_hazards", "Potential Hazards & Verification Mandates")}
              </h4>
              <div className="space-y-2">
                {potentialHazards.map((c, idx) => (
                  <div
                    key={idx}
                    className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-2.5"
                  >
                    <span className="font-bold text-slate-100">{c.concern || c.label || "Potential Hazard"}</span>
                    {c.reason && <p className="text-slate-300 mt-1">{c.reason}</p>}
                    <p className="text-[10px] text-amber-300 font-semibold mt-1">
                      {t("report.human_verification_mandate", "⚠️ Human verification mandatory prior to response intervention.")}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Disclaimers */}
          <div className="rounded-xl border border-red-950/80 bg-red-950/30 p-3 text-[11px] text-red-300 leading-relaxed">
            <span className="font-bold uppercase block mb-1">
              {t("report.safety_limits_title", "Safety Notice & AI Operational Limits")}
            </span>
            {safetyDisclaimer}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-slate-800 px-6 py-3 bg-slate-950/60">
          <span className="text-[11px] text-slate-500">
            {t("report.powered_by", "ResQ Vision • Powered by Gemma 4 Multimodal Intelligence")}
          </span>
          <button
            onClick={onClose}
            className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700"
          >
            {t("report.btn_close", "Close Report")}
          </button>
        </div>
      </div>
    </div>
  );
}
