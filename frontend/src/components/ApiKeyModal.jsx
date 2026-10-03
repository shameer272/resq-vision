import React, { useState } from "react";
import { X, Key, ShieldCheck, ExternalLink, CheckCircle } from "lucide-react";
import { setServerApiKey } from "../services/api";
import { useLanguage } from "../context/LanguageContext";

export default function ApiKeyModal({ isOpen, onClose, systemStatus, onKeyConfigured }) {
  const { t } = useLanguage();
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  if (!isOpen) return null;

  const handleSave = async (e) => {
    e.preventDefault();
    if (!apiKeyInput.trim()) {
      setError("Please enter a valid Gemini API key");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await setServerApiKey(apiKeyInput.trim());
      setSuccessMsg(res.message);
      if (onKeyConfigured) onKeyConfigured();
      setTimeout(() => {
        onClose();
        setSuccessMsg(null);
        setApiKeyInput("");
      }, 1500);
    } catch (err) {
      setError(err.message || "Failed to set API key");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
      <div className="relative w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="flex items-center space-x-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-950/80 text-blue-400 border border-blue-800/60">
            <Key className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">{t("apikey.title", "Gemini API Key Setup")}</h3>
            <p className="text-xs text-slate-400">{t("apikey.subtitle", "Server-Side Configuration for Gemma 4")}</p>
          </div>
        </div>

        <div className="rounded-xl border border-blue-900/40 bg-blue-950/20 p-3 mb-4 text-xs text-slate-300">
          <p className="leading-relaxed">
            {t("apikey.security_notice", "Your API key is sent directly to the FastAPI backend and kept in server memory. It is never stored in browser localStorage or client-side code.")}
          </p>
          <a
            href="https://aistudio.google.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 inline-flex items-center space-x-1 text-blue-400 hover:underline font-semibold"
          >
            <span>{t("apikey.free_key_link", "Get a free key from Google AI Studio")}</span>
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>

        {systemStatus?.gemini_api_key_configured && (
          <div className="mb-4 flex items-center space-x-2 rounded-lg bg-emerald-950/40 border border-emerald-800/50 p-2.5 text-xs text-emerald-300">
            <CheckCircle className="h-4 w-4 shrink-0 text-emerald-400" />
            <span>{t("apikey.active_key_notice", "Server currently has an active Gemini key")} ({systemStatus.api_key_preview})</span>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              {t("apikey.label_input", "Enter Gemini API Key (Server-Side)")}
            </label>
            <input
              type="password"
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              placeholder="AIzaSy..."
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-950/40 border border-red-900/60 rounded p-2">
              {error}
            </p>
          )}

          {successMsg && (
            <p className="text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-900/60 rounded p-2">
              {successMsg}
            </p>
          )}

          <div className="flex items-center justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-700 bg-slate-800 px-3.5 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700"
            >
              {t("apikey.btn_cancel", "Cancel")}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-blue-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
            >
              {loading ? t("apikey.btn_saving", "Saving...") : t("apikey.btn_save", "Save Server Key")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
