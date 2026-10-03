import React, { createContext, useContext, useState, useEffect } from "react";
import { translations } from "../i18n/translations";

const LanguageContext = createContext({
  language: "en",
  setLanguage: () => {},
  t: (key, fallback = "") => fallback || key,
});

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    try {
      const saved = localStorage.getItem("resq_vision_lang");
      if (saved && ["en", "te", "hi"].includes(saved)) {
        return saved;
      }
    } catch (e) {
      // LocalStorage access might fail in private windows
    }
    return "en";
  });

  const setLanguage = (newLang) => {
    if (!["en", "te", "hi"].includes(newLang)) return;
    setLanguageState(newLang);
    try {
      localStorage.setItem("resq_vision_lang", newLang);
    } catch (e) {
      // ignore
    }
  };

  const t = (key, fallback = "") => {
    const langDict = translations[language];
    if (langDict && langDict[key] !== undefined) {
      return langDict[key];
    }
    // Fallback to English
    const enDict = translations["en"];
    if (enDict && enDict[key] !== undefined) {
      return enDict[key];
    }
    return fallback || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}

export default LanguageContext;
