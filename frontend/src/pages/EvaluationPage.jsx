import React, { useState, useEffect } from "react";
import {
  BarChart3,
  ShieldCheck,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCw,
  Clock,
  Layers,
  FileCheck,
  Cpu,
  Info,
  AlertCircle,
  XCircle,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";
import { getEvaluation, runLiveEvaluation } from "../services/api";
import { useLanguage } from "../context/LanguageContext";

export default function EvaluationPage() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState("live"); // "live" | "regression"

  // Local regression state
  const [regressionMetrics, setRegressionMetrics] = useState(null);
  const [regressionLoading, setRegressionLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState("all");

  // Live Gemma 4 evaluation state
  const [liveMetrics, setLiveMetrics] = useState(null);
  const [liveLoading, setLiveLoading] = useState(false);
  const [liveCount, setLiveCount] = useState(3);
  const [liveError, setLiveError] = useState(null);

  const fetchRegressionMetrics = async () => {
    try {
      setRegressionLoading(true);
      const data = await getEvaluation();
      setRegressionMetrics(data);
    } catch (err) {
      console.error("Local regression evaluation error:", err);
    } finally {
      setRegressionLoading(false);
    }
  };

  const handleRunLiveEvaluation = async () => {
    try {
      setLiveLoading(true);
      setLiveError(null);
      const data = await runLiveEvaluation(liveCount);
      setLiveMetrics(data);
    } catch (err) {
      console.error("Live Gemma 4 evaluation error:", err);
      setLiveError(err.message || "Failed to execute live Gemma 4 evaluation.");
    } finally {
      setLiveLoading(false);
    }
  };

  useEffect(() => {
    fetchRegressionMetrics();
  }, []);

  const regressionChartData = regressionMetrics
    ? [
        { name: "Schema Validation", rate: (regressionMetrics.schema_validation_success_rate * 100).toFixed(1) },
        { name: "Structured Output", rate: (regressionMetrics.structured_output_success_rate * 100).toFixed(1) },
        { name: "Field Completion", rate: (regressionMetrics.required_field_completion_rate * 100).toFixed(1) },
        { name: "Tool Invocation", rate: (regressionMetrics.tool_call_success_rate * 100).toFixed(1) },
        { name: "Multilingual Fidelity", rate: (regressionMetrics.multilingual_fidelity_rate * 100).toFixed(1) },
      ]
    : [];

  const liveChartData = liveMetrics
    ? [
        { name: "Schema Compliance", rate: (liveMetrics.schema_compliance_rate * 100).toFixed(1) },
        { name: "Field Completion", rate: (liveMetrics.required_field_completion_rate * 100).toFixed(1) },
        { name: "Evidence Coverage", rate: (liveMetrics.evidence_completion_rate * 100).toFixed(1) },
        { name: "Safety Validation", rate: (liveMetrics.safety_validation_pass_rate * 100).toFixed(1) },
        { name: "Tool Execution", rate: (liveMetrics.tool_execution_rate * 100).toFixed(1) },
      ]
    : [];

  const scenarios = regressionMetrics?.scenarios_summary || [];
  const filteredScenarios =
    selectedCategory === "all"
      ? scenarios
      : scenarios.filter((s) => s.category === selectedCategory);

  const categories = Array.from(new Set(scenarios.map((s) => s.category)));

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-6 w-6 text-red-500" />
            <h1 className="text-2xl font-bold text-white">
              {t("eval.title", "System Evaluation & Benchmark Suite")}
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {t("eval.subtitle", "Dual evaluation engine: Real Gemma 4 multimodal inference benchmarks alongside automated local pipeline regression suites.")}
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center space-x-1.5 rounded-lg border border-slate-800 bg-slate-900/80 p-1">
          <button
            onClick={() => setActiveTab("live")}
            className={`flex items-center space-x-2 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
              activeTab === "live"
                ? "bg-red-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Zap className="h-3.5 w-3.5" />
            <span>{t("eval.tab_live", "Live Gemma 4 Evaluation")}</span>
          </button>
          <button
            onClick={() => setActiveTab("regression")}
            className={`flex items-center space-x-2 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
              activeTab === "regression"
                ? "bg-slate-800 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>{t("eval.tab_regression", "Local Pipeline Regression")}</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TAB A: LIVE GEMMA 4 EVALUATION                                           */}
      {/* ========================================================================= */}
      {activeTab === "live" && (
        <div className="space-y-6">
          {/* Controls & Configuration Card */}
          <div className="rounded-2xl border border-red-950/60 bg-gradient-to-br from-slate-900/90 via-slate-950 to-slate-900/80 p-5 shadow-xl space-y-4">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2.5">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-red-600/20 text-red-400 border border-red-500/30">
                    <Cpu className="h-4 w-4" />
                  </span>
                  <div>
                    <h2 className="text-base font-bold text-white">{t("eval.live_heading", "Live Gemma 4 Evaluation")}</h2>
                    <p className="text-xs text-slate-400">
                      {t("eval.live_desc", "Run selected benchmark scenarios through the actual Gemma 4 model and measure real inference results.")}
                    </p>
                  </div>
                </div>
              </div>

              {/* Model Identification Badge */}
              <div className="flex items-center space-x-3 text-xs">
                <div className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-slate-300">
                  <span className="text-slate-500 mr-1.5">Model:</span>
                  <span className="font-semibold text-white">Gemma 4 31B IT</span>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-slate-300">
                  <span className="text-slate-500 mr-1.5">Model ID:</span>
                  <span className="font-mono text-red-400 font-bold">gemma-4-31b-it</span>
                </div>
              </div>
            </div>

            {/* Run Controls */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-3 border-t border-slate-800/80">
              <div className="flex items-center space-x-3">
                <span className="text-xs font-medium text-slate-300">{t("eval.scenarios_label", "Scenario Batch Size:")}</span>
                <div className="flex items-center space-x-1">
                  {[1, 3, 5, 20].map((num) => (
                    <button
                      key={num}
                      type="button"
                      disabled={liveLoading}
                      onClick={() => setLiveCount(num)}
                      className={`px-3 py-1 rounded-md text-xs font-semibold border transition-colors ${
                        liveCount === num
                          ? "bg-red-600/20 border-red-500 text-red-300 font-bold"
                          : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      {num === 20 ? "All 20" : `${num} Scenario${num > 1 ? "s" : ""}`}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={handleRunLiveEvaluation}
                disabled={liveLoading}
                className="flex items-center justify-center space-x-2 rounded-xl bg-red-600 px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-red-900/30 hover:bg-red-500 disabled:opacity-50 transition-all"
              >
                <RotateCw className={`h-4 w-4 ${liveLoading ? "animate-spin" : ""}`} />
                <span>
                  {liveLoading
                    ? t("eval.btn_running", "Running selected scenarios through Gemma 4...")
                    : `${t("eval.btn_run_live", "Run Live Gemma 4 Evaluation")} (${liveCount === 20 ? "All 20" : liveCount})`}
                </span>
              </button>
            </div>

            {/* Quota & Operational Notice */}
            <div className="flex items-start space-x-2.5 rounded-xl border border-amber-900/50 bg-amber-950/20 p-3 text-xs text-amber-300/90">
              <Info className="h-4 w-4 shrink-0 text-amber-400 mt-0.5" />
              <p className="leading-relaxed">
                <span className="font-semibold text-amber-300">Live Inference Notice:</span> Live evaluation sends selected scenarios to Gemma 4 and may use API quota. Results and latency represent actual model inference.
              </p>
            </div>

            {/* Error Banner */}
            {liveError && (
              <div className="flex items-start space-x-2.5 rounded-xl border border-red-900/60 bg-red-950/30 p-3 text-xs text-red-300">
                <AlertCircle className="h-4 w-4 shrink-0 text-red-400 mt-0.5" />
                <div>
                  <span className="font-semibold text-red-200">Gemma 4 Live Inference Error:</span>
                  <p className="mt-0.5 font-mono text-[11px] text-red-300">{liveError}</p>
                </div>
              </div>
            )}
          </div>

          {/* Live KPI Cards */}
          {liveMetrics && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">
                  {t("eval.scenarios_evaluated", "Scenarios Executed")}
                </span>
                <div className="text-2xl font-black text-white">
                  {liveMetrics.scenarios_executed}
                </div>
                <span className="text-[10px] text-slate-400">
                  {liveMetrics.successful_calls} successful / {liveMetrics.failed_calls} failed
                </span>
              </div>

              <div className="rounded-xl border border-emerald-900/60 bg-emerald-950/20 p-4">
                <span className="text-[10px] uppercase font-bold text-emerald-400 block mb-1">
                  {t("eval.compliance_rate", "Schema Compliance")}
                </span>
                <div className="text-2xl font-black text-emerald-300">
                  {(liveMetrics.schema_compliance_rate * 100).toFixed(1)}%
                </div>
                <span className="text-[10px] text-emerald-500">Strict Pydantic typing</span>
              </div>

              <div className="rounded-xl border border-blue-900/60 bg-blue-950/20 p-4">
                <span className="text-[10px] uppercase font-bold text-blue-400 block mb-1">
                  {t("eval.field_completion", "Field Completion")}
                </span>
                <div className="text-2xl font-black text-blue-300">
                  {(liveMetrics.required_field_completion_rate * 100).toFixed(1)}%
                </div>
                <span className="text-[10px] text-blue-400">Mandated keys present</span>
              </div>

              <div className="rounded-xl border border-purple-900/60 bg-purple-950/20 p-4">
                <span className="text-[10px] uppercase font-bold text-purple-400 block mb-1">
                  {t("eval.evidence_rate", "Evidence Coverage")}
                </span>
                <div className="text-2xl font-black text-purple-300">
                  {(liveMetrics.evidence_completion_rate * 100).toFixed(1)}%
                </div>
                <span className="text-[10px] text-purple-400">Auditable image cues</span>
              </div>

              <div className="rounded-xl border border-amber-900/60 bg-amber-950/20 p-4">
                <span className="text-[10px] uppercase font-bold text-amber-400 block mb-1">
                  {t("eval.safety_rate", "Safety Validation")}
                </span>
                <div className="text-2xl font-black text-amber-300">
                  {(liveMetrics.safety_validation_pass_rate * 100).toFixed(1)}%
                </div>
                <span className="text-[10px] text-amber-500">Guardrails verified</span>
              </div>

              <div className="rounded-xl border border-cyan-900/60 bg-cyan-950/20 p-4">
                <span className="text-[10px] uppercase font-bold text-cyan-400 block mb-1">
                  RAG Citation Presence
                </span>
                <div className="text-2xl font-black text-cyan-300">
                  {(liveMetrics.rag_citation_rate * 100).toFixed(1)}%
                </div>
                <span className="text-[10px] text-cyan-500">Protocol references</span>
              </div>

              <div className="rounded-xl border border-indigo-900/60 bg-indigo-950/20 p-4">
                <span className="text-[10px] uppercase font-bold text-indigo-400 block mb-1">
                  {t("eval.tool_rate", "Tool Execution")}
                </span>
                <div className="text-2xl font-black text-indigo-300">
                  {(liveMetrics.tool_execution_rate * 100).toFixed(1)}%
                </div>
                <span className="text-[10px] text-indigo-400">Checklist & location</span>
              </div>

              <div className="rounded-xl border border-red-950/80 bg-red-950/20 p-4 col-span-2 sm:col-span-3 lg:col-span-3">
                <span className="text-[10px] uppercase font-bold text-red-400 block mb-1">
                  Average Gemma 4 inference latency
                </span>
                <div className="flex items-baseline space-x-2">
                  <span className="text-3xl font-black text-red-200">
                    {liveMetrics.average_inference_latency_seconds}s
                  </span>
                  <span className="text-xs text-slate-400">
                    per multimodal request (measured directly across Gemma 4 API calls)
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Visual Bar Chart for Live Results */}
          {liveMetrics && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Live Gemma 4 Metric Pass Rates (%)
                </h3>
                <span className="text-xs text-red-400 font-medium">Real Gemma 4 Inference Data</span>
              </div>
              <div className="h-60 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={liveChartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                    <XAxis dataKey="name" stroke="#64748b" fontSize={11} interval={0} angle={-15} textAnchor="end" />
                    <YAxis domain={[0, 100]} stroke="#64748b" fontSize={11} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", color: "#f8fafc", fontSize: "12px" }}
                    />
                    <Bar dataKey="rate" radius={[4, 4, 0, 0]}>
                      {liveChartData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={
                            index === 0 ? "#10b981" : index === 1 ? "#3b82f6" : index === 2 ? "#8b5cf6" : index === 3 ? "#f59e0b" : "#06b6d4"
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Live Gemma 4 Results Table */}
          {liveMetrics && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                    LIVE GEMMA 4 RESULTS ({liveMetrics.scenario_results.length} Scenarios Executed)
                  </h3>
                  <p className="text-xs text-slate-400">
                    Actual responses, strict Pydantic compliance, evidence verification, and measured inference latencies.
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950/80 text-[10px] uppercase font-bold text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">ID</th>
                      <th className="py-2.5 px-3">Category</th>
                      <th className="py-2.5 px-3">Scenario Title</th>
                      <th className="py-2.5 px-3 text-center">Gemma 4 Status</th>
                      <th className="py-2.5 px-3 text-center">Schema</th>
                      <th className="py-2.5 px-3 text-center">Fields</th>
                      <th className="py-2.5 px-3 text-center">Evidence</th>
                      <th className="py-2.5 px-3 text-center">RAG</th>
                      <th className="py-2.5 px-3 text-center">Tools</th>
                      <th className="py-2.5 px-3 text-center">Safety</th>
                      <th className="py-2.5 px-3 text-right">Latency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {liveMetrics.scenario_results.map((scen) => (
                      <tr key={scen.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2 px-3 font-mono font-bold text-red-400">{scen.id}</td>
                        <td className="py-2 px-3">
                          <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] uppercase font-semibold text-slate-300">
                            {scen.category.replace(/_/g, " ")}
                          </span>
                        </td>
                        <td className="py-2 px-3 font-medium text-slate-100 max-w-xs truncate" title={scen.title}>
                          {scen.title}
                        </td>
                        <td className="py-2 px-3 text-center">
                          {scen.gemma_status === "passed" ? (
                            <span className="text-emerald-400 font-semibold">✓ Passed</span>
                          ) : scen.gemma_status === "error" ? (
                            <span className="text-amber-400 font-semibold" title={scen.error_message || ""}>⚠ Error</span>
                          ) : (
                            <span className="text-red-400 font-semibold" title={scen.error_message || ""}>✕ Failed</span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-center">
                          {scen.schema_valid ? (
                            <span className="text-emerald-400">✓ Valid</span>
                          ) : (
                            <span className="text-red-400">✕ Invalid</span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-center">
                          {scen.fields_complete ? (
                            <span className="text-emerald-400">✓ 100%</span>
                          ) : (
                            <span className="text-amber-400">Partial</span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-center">
                          {scen.evidence_coverage ? (
                            <span className="text-purple-400">✓ Linked</span>
                          ) : (
                            <span className="text-slate-500">—</span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-center">
                          {scen.rag_citations_present ? (
                            <span className="text-blue-400">✓ Cited</span>
                          ) : (
                            <span className="text-slate-500">—</span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-center">
                          {scen.tools_executed ? (
                            <span className="text-indigo-400">✓ Active</span>
                          ) : (
                            <span className="text-slate-500">—</span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-center">
                          {scen.safety_pass ? (
                            <span className="text-emerald-400">✓ Passed</span>
                          ) : (
                            <span className="text-amber-400">Filtered</span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-right font-mono font-bold text-slate-300">
                          {scen.inference_latency_sec > 0 ? `${scen.inference_latency_sec}s` : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Empty Prompt when not yet run */}
          {!liveMetrics && !liveLoading && (
            <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center space-y-3">
              <Zap className="h-10 w-10 text-red-500/60 mx-auto" />
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Awaiting Live Evaluation Execution
              </h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
                Select your desired scenario batch size (1, 3, 5, or All 20) and click{" "}
                <span className="text-red-400 font-semibold">"Run Live Gemma 4 Evaluation"</span> to invoke the production Gemma 4 31B IT model, validate outputs against strict Pydantic schemas, and record real inference latencies.
              </p>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB B: LOCAL PIPELINE REGRESSION                                         */}
      {/* ========================================================================= */}
      {activeTab === "regression" && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <Layers className="h-5 w-5 text-slate-400" />
                  <h2 className="text-base font-bold text-white">{t("eval.reg_heading", "Local Pipeline Regression Suite")}</h2>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  {t("eval.reg_desc", "These 20 scenarios validate local schema, RAG, safety, and tool integration. They do not perform live Gemma 4 inference.")}
                </p>
              </div>

              <button
                onClick={fetchRegressionMetrics}
                disabled={regressionLoading}
                className="flex items-center space-x-1.5 rounded-lg bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 disabled:opacity-50"
              >
                <RotateCw className={`h-3.5 w-3.5 ${regressionLoading ? "animate-spin" : ""}`} />
                <span>{regressionLoading ? "Testing..." : "Re-Run Regression"}</span>
              </button>
            </div>
          </div>

          {/* Regression KPI Cards */}
          {regressionMetrics && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">
                  Scenarios Tested
                </span>
                <div className="text-2xl font-black text-white">
                  {regressionMetrics.total_scenarios_evaluated}
                </div>
                <span className="text-[10px] text-slate-400">10 distinct categories</span>
              </div>

              <div className="rounded-xl border border-emerald-900/60 bg-emerald-950/20 p-4">
                <span className="text-[10px] uppercase font-bold text-emerald-400 block mb-1">
                  Schema Compliance
                </span>
                <div className="text-2xl font-black text-emerald-300">
                  {(regressionMetrics.schema_validation_success_rate * 100).toFixed(1)}%
                </div>
                <span className="text-[10px] text-emerald-500">Pydantic strict typing</span>
              </div>

              <div className="rounded-xl border border-blue-900/60 bg-blue-950/20 p-4">
                <span className="text-[10px] uppercase font-bold text-blue-400 block mb-1">
                  Field Completion
                </span>
                <div className="text-2xl font-black text-blue-300">
                  {(regressionMetrics.required_field_completion_rate * 100).toFixed(1)}%
                </div>
                <span className="text-[10px] text-blue-400">All mandated keys</span>
              </div>

              <div className="rounded-xl border border-purple-900/60 bg-purple-950/20 p-4">
                <span className="text-[10px] uppercase font-bold text-purple-400 block mb-1">
                  Tool Success Rate
                </span>
                <div className="text-2xl font-black text-purple-300">
                  {(regressionMetrics.tool_call_success_rate * 100).toFixed(1)}%
                </div>
                <span className="text-[10px] text-purple-400">Safe tool allowlist</span>
              </div>

              <div className="rounded-xl border border-amber-900/60 bg-amber-950/20 p-4">
                <span className="text-[10px] uppercase font-bold text-amber-400 block mb-1">
                  Safety Sanitizations
                </span>
                <div className="text-2xl font-black text-amber-300">
                  {regressionMetrics.safety_rule_violations_caught}
                </div>
                <span className="text-[10px] text-amber-500">Hazards tempered</span>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">
                  Local CPU Latency
                </span>
                <div className="text-2xl font-black text-white">
                  {regressionMetrics.average_latency_seconds}s
                </div>
                <span className="text-[10px] text-slate-400">In-memory execution</span>
              </div>
            </div>
          )}

          {/* Recharts Visualization */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-8 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Operational Performance Benchmark Rates (%)
                </h3>
                <span className="text-xs text-slate-400 font-medium">Local Pipeline Regression Data</span>
              </div>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={regressionChartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                    <XAxis dataKey="name" stroke="#64748b" fontSize={11} interval={0} angle={-15} textAnchor="end" />
                    <YAxis domain={[0, 100]} stroke="#64748b" fontSize={11} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", color: "#f8fafc", fontSize: "12px" }}
                    />
                    <Bar dataKey="rate" fill="#ef4444" radius={[4, 4, 0, 0]}>
                      {regressionChartData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={
                            index === 0 ? "#10b981" : index === 1 ? "#3b82f6" : index === 2 ? "#8b5cf6" : "#f59e0b"
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Safety & Protocol Compliance notes */}
            <div className="lg:col-span-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg space-y-3 text-xs">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-2">
                Safety & Ethical Guardrails
              </h3>

              <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                <span className="font-semibold text-emerald-400 block mb-1">
                  Zero Unsupported Claims
                </span>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Every single extracted observation must specify an auditable evidence string linked to image features.
                </p>
              </div>

              <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                <span className="font-semibold text-amber-400 block mb-1">
                  No Medical Diagnosis
                </span>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Medical conditions are converted to descriptive physical distress notes requiring qualified triage.
                </p>
              </div>

              <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                <span className="font-semibold text-red-400 block mb-1">
                  Bystander Protection
                </span>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Action instructions to touch high-voltage wires or enter burning buildings are automatically rewritten into safe stand-off perimeters.
                </p>
              </div>
            </div>
          </div>

          {/* Controlled Test Scenarios Table */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Regression Scenario Results ({filteredScenarios.length} Scenarios)
                </h3>
                <p className="text-xs text-slate-400">
                  Detailed validation, RAG citations, and local execution latency per test case
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <span className="text-xs text-slate-400">Category:</span>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 focus:outline-none"
                >
                  <option value="all">All Categories</option>
                  {categories.map((c) => (
                    <option key={c} value={c}>
                      {c.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-[10px] uppercase font-bold text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">ID</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3">Scenario Title</th>
                    <th className="py-2.5 px-3 text-center">Schema Valid</th>
                    <th className="py-2.5 px-3 text-center">Fields Complete</th>
                    <th className="py-2.5 px-3 text-center">RAG Citations</th>
                    <th className="py-2.5 px-3 text-center">Tools Executed</th>
                    <th className="py-2.5 px-3 text-right">CPU Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredScenarios.map((scen) => (
                    <tr key={scen.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-2 px-3 font-mono font-bold text-red-400">{scen.id}</td>
                      <td className="py-2 px-3">
                        <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] uppercase font-semibold text-slate-300">
                          {scen.category.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="py-2 px-3 font-medium text-slate-100">{scen.title}</td>
                      <td className="py-2 px-3 text-center">
                        {scen.schema_valid ? (
                          <span className="text-emerald-400">✓ Passed</span>
                        ) : (
                          <span className="text-red-400">✗ Failed</span>
                        )}
                      </td>
                      <td className="py-2 px-3 text-center">
                        {scen.fields_complete ? (
                          <span className="text-emerald-400">✓ 100%</span>
                        ) : (
                          <span className="text-amber-400">Partial</span>
                        )}
                      </td>
                      <td className="py-2 px-3 text-center">
                        {scen.rag_retrieval_ok ? (
                          <span className="text-blue-400">✓ Curated</span>
                        ) : (
                          <span className="text-slate-500">—</span>
                        )}
                      </td>
                      <td className="py-2 px-3 text-center">
                        {scen.tools_ok ? (
                          <span className="text-purple-400">✓ Active</span>
                        ) : (
                          <span className="text-slate-500">—</span>
                        )}
                      </td>
                      <td className="py-2 px-3 text-right font-mono text-slate-400">
                        {scen.latency_sec}s
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
