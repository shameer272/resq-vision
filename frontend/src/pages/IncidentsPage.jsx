import React, { useState, useEffect } from "react";
import {
  Clock,
  Search,
  Filter,
  Trash2,
  ExternalLink,
  FileText,
  Download,
  AlertTriangle,
  RefreshCw,
  MapPin,
  CheckCircle,
} from "lucide-react";
import { getIncidents, deleteIncident, exportPdf, generateReport } from "../services/api";
import ReportModal from "../components/ReportModal";
import { useLanguage } from "../context/LanguageContext";

export default function IncidentsPage({ setActiveTab, onSelectIncident }) {
  const { t } = useLanguage();
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [selectedReport, setSelectedReport] = useState(null);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);

  const fetchIncidents = async () => {
    try {
      setLoading(true);
      const data = await getIncidents();
      setIncidents(data);
    } catch (err) {
      console.error("Failed to load incidents:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, []);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm(`Delete incident ${id} from system records?`)) return;
    try {
      await deleteIncident(id);
      setIncidents((prev) => prev.filter((inc) => inc.incident_id !== id));
    } catch (err) {
      alert("Failed to delete: " + err.message);
    }
  };

  const handleExport = async (incident, e) => {
    e.stopPropagation();
    try {
      await exportPdf(incident);
    } catch (err) {
      alert("PDF download failed: " + err.message);
    }
  };

  const handleOpenReport = async (incident) => {
    setSelectedIncident(incident);
    setIsReportOpen(true);
    if (incident.methane_structure) {
      setSelectedReport(incident);
      return;
    }
    setSelectedReport(incident);
    setLoadingReport(true);
    try {
      const fullReport = await generateReport(incident);
      setSelectedReport(fullReport);
    } catch (err) {
      console.error("Error generating METHANE report:", err);
    } finally {
      setLoadingReport(false);
    }
  };

  const filtered = incidents.filter((inc) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      (inc.incident_id || "").toLowerCase().includes(q) ||
      (inc.incident_summary || "").toLowerCase().includes(q) ||
      (inc.location || "").toLowerCase().includes(q);

    const matchesType =
      filterType === "all" || (inc.incident_type || "").toLowerCase().includes(filterType);

    return matchesSearch && matchesType;
  });

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Clock className="h-6 w-6 text-red-500" />
            <h1 className="text-2xl font-bold text-white">{t("incidents.title", "Incident Registry & History")}</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {t("incidents.subtitle", "Persisted operational records (Stored via MongoDB or Local JSON Database)")}
          </p>
        </div>

        <button
          onClick={fetchIncidents}
          className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3.5 py-2 text-xs font-medium text-slate-200 hover:bg-slate-700"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>{t("incidents.btn_refresh", "Refresh")}</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t("incidents.search_placeholder", "Search by Incident ID, summary, or location...")}
            className="w-full rounded-xl border border-slate-700 bg-slate-900 pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:border-red-500 focus:outline-none"
          />
        </div>

        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-slate-500 shrink-0" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:border-red-500 focus:outline-none"
          >
            <option value="all">{t("incidents.filter_all", "All Incident Types")}</option>
            <option value="road">{t("incidents.filter_road", "Road Collisions")}</option>
            <option value="fire">{t("incidents.filter_fire", "Smoke / Fire")}</option>
            <option value="flood">{t("incidents.filter_flood", "Flooding")}</option>
            <option value="block">{t("incidents.filter_block", "Road Obstructions")}</option>
          </select>
        </div>
      </div>

      {/* Incident List */}
      {loading ? (
        <div className="py-16 text-center text-slate-400 text-xs">
          {t("incidents.loading", "Loading incident history...")}
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <Clock className="mx-auto h-8 w-8 text-slate-600 mb-3" />
          <h3 className="text-sm font-semibold text-slate-300">{t("incidents.none_found", "No Incidents Found")}</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            {searchQuery
              ? t("incidents.none_search", "No records matched your filter criteria.")
              : t("incidents.none_analyzed", "No incidents analyzed yet. Run an analysis on the Analyze tab.")}
          </p>
          <button
            onClick={() => setActiveTab("analyze")}
            className="mt-4 rounded-xl bg-red-600 px-4 py-2 text-xs font-semibold text-white hover:bg-red-500"
          >
            {t("incidents.btn_start", "Start New Analysis")}
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((inc) => (
            <div
              key={inc.incident_id}
              onClick={() => handleOpenReport(inc)}
              className="group flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-5 transition-all hover:border-slate-700 hover:bg-slate-900/90 cursor-pointer shadow-md"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold text-red-400">
                    {inc.incident_id}
                  </span>
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] uppercase font-bold text-slate-300">
                    {inc.incident_type?.replace(/_/g, " ")}
                  </span>
                </div>

                <h4 className="text-sm font-semibold text-white line-clamp-2 mb-2">
                  {inc.incident_summary}
                </h4>

                {inc.location && (
                  <div className="flex items-center text-[11px] text-slate-400 mb-2">
                    <MapPin className="h-3 w-3 mr-1 text-slate-500 shrink-0" />
                    <span className="truncate">{inc.location}</span>
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                <span>{new Date(inc.timestamp || Date.now()).toLocaleDateString()}</span>

                <div className="flex items-center space-x-1.5">
                  <button
                    onClick={(e) => handleExport(inc, e)}
                    className="p-1 text-slate-400 hover:text-white"
                    title={t("incidents.export_pdf", "Export PDF")}
                  >
                    <Download className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={(e) => handleDelete(inc.incident_id, e)}
                    className="p-1 text-slate-400 hover:text-red-400"
                    title={t("incidents.delete_record", "Delete record")}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Report Modal */}
      {(selectedReport || selectedIncident) && (
        <ReportModal
          isOpen={isReportOpen}
          onClose={() => {
            setIsReportOpen(false);
            setSelectedReport(null);
            setSelectedIncident(null);
          }}
          reportData={selectedReport}
          incidentData={selectedIncident}
          loading={loadingReport}
        />
      )}
    </div>
  );
}
