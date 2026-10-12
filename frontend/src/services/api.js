export const getApiBaseUrl = (env = import.meta.env) => {
  const envUrl = env?.VITE_API_BASE_URL;
  if (envUrl && typeof envUrl === "string" && envUrl.trim()) {
    return envUrl.trim().replace(/\/+$/, "");
  }
  // In development, default to local FastAPI server on port 8000
  if (env?.DEV) {
    return "http://127.0.0.1:8000";
  }
  // Production default pointing to the deployed backend
  return "https://resq-vision-71gv.vercel.app";
};

export const API_BASE = getApiBaseUrl();

export async function checkHealth() {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function setServerApiKey(apiKey) {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/config/api-key`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to configure API key" }));
    throw new Error(err.detail || "Failed to configure API key");
  }
  return res.json();
}

export async function setServerDOToken(token) {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/config/do-token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to configure DigitalOcean token" }));
    throw new Error(err.detail || "Failed to configure DigitalOcean token");
  }
  return res.json();
}

export async function setServerAIProvider(provider) {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/config/provider`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to set provider" }));
    throw new Error(err.detail || "Failed to set provider");
  }
  return res.json();
}

export async function analyzeIncident(formData) {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/analyze`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Analysis failed" }));
    throw new Error(err.detail || err.message || `Server error (${res.status})`);
  }
  return res.json();
}

export async function analyzeMultiImage(formData) {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/analyze/multi-image`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Multi-image analysis failed" }));
    throw new Error(err.detail || err.message || `Server error (${res.status})`);
  }
  return res.json();
}

export async function generateReport(incidentData) {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/incident/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(incidentData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Report generation failed" }));
    throw new Error(err.detail || "Report generation failed");
  }
  return res.json();
}

export async function generateChecklist(incidentData) {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/incident/checklist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(incidentData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Checklist generation failed" }));
    throw new Error(err.detail || "Checklist generation failed");
  }
  return res.json();
}

export async function translateIncident(incidentData, targetLanguage) {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: incidentData.incident_summary || "",
      target_language: targetLanguage,
      preserve_uncertainty: true,
      incident_data: incidentData,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Translation failed" }));
    throw new Error(err.detail || "Translation failed");
  }
  return res.json();
}

export async function getIncidents() {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/incidents`);
  if (!res.ok) throw new Error("Failed to load incident history");
  return res.json();
}

export async function getIncidentById(id) {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/incidents/${id}`);
  if (!res.ok) throw new Error("Incident not found");
  return res.json();
}

export async function deleteIncident(id) {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/incidents/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete incident");
  return res.json();
}

export async function exportPdf(reportData) {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/export?format=pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(reportData),
  });
  if (!res.ok) throw new Error("Failed to generate PDF");
  const blob = await res.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = `ResQ_Vision_Report_${reportData.incident_id || "incident"}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

export async function getEvaluation() {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/evaluation`);
  if (!res.ok) throw new Error("Failed to run local regression benchmark suite");
  return res.json();
}

export async function runLiveEvaluation(count = 3, scenarioIds = null) {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/evaluation/live`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      count,
      scenario_ids: scenarioIds,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Live Gemma 4 evaluation failed" }));
    throw new Error(err.detail || err.message || `Server error (${res.status})`);
  }
  return res.json();
}

export async function getDemoScenarios() {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/demo-scenarios`);
  if (!res.ok) throw new Error("Failed to load demonstration scenarios");
  return res.json();
}

export async function saveIncidentEndpoint(incidentData) {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/incident/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ incident_data: incidentData }),
  });
  if (!res.ok) throw new Error("Failed to save incident record");
  return res.json();
}

export async function runAgentWorkflow(incidentData, goals) {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/agent/workflow`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      incident_data: incidentData,
      goals: goals || ["location_context", "safety_guidance", "checklist", "report", "save"],
    }),
  });
  if (!res.ok) throw new Error("Agent workflow execution failed");
  return res.json();
}
