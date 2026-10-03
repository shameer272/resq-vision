import React, { useState } from "react";
import {
  ShieldAlert,
  Activity,
  Cpu,
  FileText,
  Clock,
  BarChart3,
  Sparkles,
  Info,
  Key,
  Globe,
  Radio,
} from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export default function Navbar({
  activeTab,
  setActiveTab,
  systemStatus,
  onOpenApiKeyModal,
  selectedLanguage: propLanguage,
  setSelectedLanguage: propSetLanguage,
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { language, setLanguage, t } = useLanguage();

  const currentLanguage = propLanguage || language;
  const changeLanguage = (lang) => {
    if (propSetLanguage) propSetLanguage(lang);
    setLanguage(lang);
  };

  const navLinks = [
    { id: "analyze", label: t("nav.analyze", "Analyze"), icon: Activity },
    { id: "incidents", label: t("nav.incidents", "Incidents"), icon: Clock },
    { id: "evaluation", label: t("nav.evaluation", "Evaluation"), icon: BarChart3 },
    { id: "demo", label: t("nav.demo", "Demo Scenarios"), icon: Sparkles },
    { id: "about", label: t("nav.about", "About & Tech"), icon: Info },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        {/* Brand */}
        <div
          onClick={() => setActiveTab("landing")}
          className="flex cursor-pointer items-center space-x-3 transition-opacity hover:opacity-90"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-red-600 to-rose-700 text-white shadow-lg shadow-red-900/30">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight text-white">
                RESQ <span className="text-red-500">VISION</span>
              </span>
              <span className="rounded bg-red-950/80 px-2 py-0.5 text-[10px] font-semibold tracking-wider text-red-300 border border-red-800/60 uppercase">
                {t("brand.badge", "Emergency Intel")}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              {t("brand.tagline", "Multimodal Emergency Situation Intelligence")}
            </p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="hidden md:flex items-center space-x-1">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = activeTab === link.id;
            return (
              <button
                key={link.id}
                onClick={() => setActiveTab(link.id)}
                className={`flex items-center space-x-2 rounded-md px-3.5 py-2 text-sm font-medium transition-all ${
                  isActive
                    ? "bg-slate-800 text-white shadow-sm border border-slate-700"
                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? "text-red-400" : "text-slate-500"}`} />
                <span>{link.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Status Badges & Quick Controls */}
        <div className="flex items-center space-x-2.5">
          {/* Gemma 4 Model Badge */}
          <div className="hidden lg:flex items-center space-x-1.5 rounded-full border border-blue-900/50 bg-blue-950/40 px-3 py-1 text-xs text-blue-300">
            <Cpu className="h-3.5 w-3.5 text-blue-400 animate-pulse" />
            <span className="font-semibold">{t("nav.model_badge", "Gemma 4")}</span>
            <span className="text-blue-500 text-[10px]">{t("nav.model_sub", "(31B-IT)")}</span>
          </div>

          {/* Multilingual Selector */}
          <div className="flex items-center rounded-lg border border-slate-800 bg-slate-900 px-2 py-1 text-xs text-slate-300">
            <Globe className="h-3.5 w-3.5 mr-1.5 text-slate-400" />
            <select
              value={currentLanguage}
              onChange={(e) => changeLanguage(e.target.value)}
              className="bg-transparent text-slate-200 text-xs focus:outline-none cursor-pointer"
            >
              <option value="en" className="bg-slate-900 text-white">English</option>
              <option value="te" className="bg-slate-900 text-white">తెలుగు (Telugu)</option>
              <option value="hi" className="bg-slate-900 text-white">हिन्दी (Hindi)</option>
            </select>
          </div>

          {/* Server Key Config Button */}
          <button
            onClick={onOpenApiKeyModal}
            title={systemStatus?.gemini_api_key_configured ? t("nav.key_active", "Key Active") : t("nav.add_key", "Add Key")}
            className={`flex items-center space-x-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-all ${
              systemStatus?.gemini_api_key_configured
                ? "border-emerald-800/80 bg-emerald-950/40 text-emerald-300 hover:bg-emerald-900/50"
                : "border-amber-800/80 bg-amber-950/40 text-amber-300 hover:bg-amber-900/50 animate-pulse"
            }`}
          >
            <Key className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">
              {systemStatus?.gemini_api_key_configured
                ? t("nav.key_active", "Key Active")
                : t("nav.add_key", "Add Key")}
            </span>
          </button>
        </div>
      </div>

      {/* Mobile nav row */}
      <div className="flex md:hidden overflow-x-auto border-t border-slate-800/70 px-3 py-2 space-x-1 bg-slate-950/95 scrollbar-none">
        {navLinks.map((link) => {
          const Icon = link.icon;
          const isActive = activeTab === link.id;
          return (
            <button
              key={link.id}
              onClick={() => setActiveTab(link.id)}
              className={`flex shrink-0 items-center space-x-1.5 rounded-md px-3 py-1.5 text-xs font-medium ${
                isActive ? "bg-slate-800 text-white border border-slate-700" : "text-slate-400"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{link.label}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
}

