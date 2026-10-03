import React, { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import ApiKeyModal from "./components/ApiKeyModal";
import LandingPage from "./pages/LandingPage";
import AnalyzePage from "./pages/AnalyzePage";
import IncidentsPage from "./pages/IncidentsPage";
import EvaluationPage from "./pages/EvaluationPage";
import DemoPage from "./pages/DemoPage";
import AboutPage from "./pages/AboutPage";
import { checkHealth } from "./services/api";
import { LanguageProvider, useLanguage } from "./context/LanguageContext";

function AppContent() {
  const [activeTab, setActiveTab] = useState("landing");
  const { language: selectedLanguage, setLanguage: setSelectedLanguage, t } = useLanguage();
  const [systemStatus, setSystemStatus] = useState(null);
  const [isApiKeyModalOpen, setIsApiKeyModalOpen] = useState(false);
  const [preloadedScenario, setPreloadedScenario] = useState(null);

  const fetchStatus = () => {
    checkHealth()
      .then((data) => setSystemStatus(data))
      .catch((err) => {
        console.warn("Backend not yet connected:", err.message);
        setSystemStatus({ status: "offline", gemini_api_key_configured: false });
      });
  };

  useEffect(() => {
    fetchStatus();
    // Refresh status periodically
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectDemo = (scenario) => {
    setPreloadedScenario(scenario);
    setActiveTab("analyze");
  };

  const handleClearPreloaded = () => {
    setPreloadedScenario(null);
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans selection:bg-red-900 selection:text-white">
      {/* Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        systemStatus={systemStatus}
        onOpenApiKeyModal={() => setIsApiKeyModalOpen(true)}
        selectedLanguage={selectedLanguage}
        setSelectedLanguage={setSelectedLanguage}
      />

      {/* Main View Area */}
      <main className="flex-1">
        {activeTab === "landing" && (
          <LandingPage
            setActiveTab={setActiveTab}
            onOpenApiKeyModal={() => setIsApiKeyModalOpen(true)}
            systemStatus={systemStatus}
          />
        )}

        {activeTab === "analyze" && (
          <AnalyzePage
            selectedLanguage={selectedLanguage}
            setSelectedLanguage={setSelectedLanguage}
            systemStatus={systemStatus}
            preloadedScenario={preloadedScenario}
            onClearPreloaded={handleClearPreloaded}
            onOpenApiKeyModal={() => setIsApiKeyModalOpen(true)}
          />
        )}

        {activeTab === "incidents" && (
          <IncidentsPage
            setActiveTab={setActiveTab}
            onSelectIncident={(inc) => {
              setPreloadedScenario(inc);
              setActiveTab("analyze");
            }}
          />
        )}

        {activeTab === "evaluation" && <EvaluationPage />}

        {activeTab === "demo" && (
          <DemoPage
            setActiveTab={setActiveTab}
            onSelectDemo={handleSelectDemo}
          />
        )}

        {activeTab === "about" && <AboutPage />}
      </main>

      {/* API Key Modal */}
      <ApiKeyModal
        isOpen={isApiKeyModalOpen}
        onClose={() => setIsApiKeyModalOpen(false)}
        systemStatus={systemStatus}
        onKeyConfigured={fetchStatus}
      />

      {/* Legal & Safety Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500 px-4">
        <div className="mx-auto max-w-7xl flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2 text-slate-400">
            <span className="font-bold text-white">{t("footer.title", "RESQ VISION")}</span>
            <span>• {t("footer.subtitle", "Multimodal Emergency Situation Intelligence")}</span>
          </div>

          <div className="text-[11px] text-slate-500">
            {t("footer.challenge", "Hacktoberfest Hack Day Hyderabad × NIAT • Target Challenge: Best Use of Gemma 4")}
          </div>

          <div className="text-[10px] text-slate-600">
            {t("footer.disclaimer", "Decision support tool only. Human verification mandatory.")}
          </div>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  );
}

