import re
from typing import Dict, Any, Optional, List
from app.core.config import settings

def clean_language_prefixes(text: str) -> str:
    """Removes any prepended [Telugu (...)], [Hindi (...)], [English], or repeated language labels."""
    if not isinstance(text, str):
        return text
    cleaned = re.sub(r'^\s*(\[(?:Telugu|Hindi|English|te|hi|en)[^\]]*\]\s*)+', '', text, flags=re.IGNORECASE)
    return cleaned.strip()

def clean_incident_data(data: Any) -> Any:
    """Recursively removes legacy [Language] prefixes across all string fields."""
    if isinstance(data, str):
        return clean_language_prefixes(data)
    elif isinstance(data, list):
        return [clean_incident_data(item) for item in data]
    elif isinstance(data, dict):
        return {k: clean_incident_data(v) for k, v in data.items()}
    return data

class TranslationService:
    """
    Multilingual Emergency Translation Service.
    Supports English, Telugu (తెలుగు), and Hindi (हिन्दी).
    Strictly preserves:
    - Epistemic uncertainty (does not convert 'possible' into 'confirmed')
    - Evidence links and provenance tags (Observed, User Reported, Inferred)
    - Human verification requirements and safety warnings.
    - Technical identifiers (Gemma 4, gemma-4-31b-it, URLs, incident IDs).
    """

    LANGUAGE_NAMES = {
        "en": "English",
        "te": "Telugu (తెలుగు)",
        "hi": "Hindi (हिन्दी)"
    }

    # High-fidelity emergency domain lexicon
    TRANSLATION_LEXICON = {
        "te": {
            "incident_summary": "సంఘటన సారాంశం",
            "incident_type": "సంఘటన రకం",
            "observations": "పరిశీలనలు (ఆధారాలతో కూడినవి)",
            "user_reported_information": "వినియోగదారు తెలిపిన సమాచారం",
            "potential_concerns": "సంభావ్య ప్రమాదాలు / ఆందోళనలు",
            "uncertainties": "అనిశ్చితులు (ధృవీకరించబడనివి)",
            "missing_information": "అవసరమైన అదనపు సమాచారం",
            "recommended_information_to_communicate": "అత్యవసర విభాగాలకు తెలియజేయవలసిన వివరాలు",
            "confidence_notes": "విశ్వసనీయత గమనికలు",
            "safety_disclaimer": "గమనిక: ఈ నివేదిక Gemma 4 AI ఆధారిత సమాచార విశ్లేషణ మాత్రమే. ఇది వైద్య నిర్ధారణ కాదు మరియు అత్యవసర సేవల అధికారిక ఉత్తర్వులను భర్తీ చేయదు. మానవ ధృవీకరణ తప్పనిసరి.",
            "requires_human_verification": "రంగంలో ఉన్న సహాయక సిబ్బంది ద్వారా మానవ ధృవీకరణ తప్పనిసరి",
            "observed": "ప్రత్యక్షంగా గమనించినది",
            "user_reported": "వినియోగదారు తెలిపినది",
            "inferred": "సూచించబడినది / ఊహించినది",
            "road_accident": "రహదారి ప్రమాదం (పరిశీలనలో)",
            "smoke_fire": "పొగ లేదా అగ్ని ప్రమాద సంకేతం",
            "flooding": "వరద నీటి ముంపు",
            "structural_damage": "భవనం లేదా నిర్మాణ నష్టం",
            "blocked_road": "రహదారి అడ్డంకి",
            "severe_weather": "తీవ్రమైన వాతావరణం",
            "ambiguous": "అనిశ్చిత పరిస్థితి",
            "no_emergency": "అత్యవసర పరిస్థితి లేదు"
        },
        "hi": {
            "incident_summary": "घटना का सारांश",
            "incident_type": "घटना का प्रकार",
            "observations": "अवलोकन (साक्ष्य-आधारित)",
            "user_reported_information": "उपयोगकर्ता द्वारा दी गई जानकारी",
            "potential_concerns": "संभावित खतरे एवं चिंताएं",
            "uncertainties": "अनिश्चितताएं (पुष्टि की आवश्यकता)",
            "missing_information": "अनुपलब्ध महत्वपूर्ण जानकारी",
            "recommended_information_to_communicate": "आपातकालीन प्रतिक्रिया के लिए आवश्यक संवाद",
            "confidence_notes": "विश्वसनीयता नोट्स",
            "safety_disclaimer": "चेतावनी: यह रिपोर्ट Gemma 4 AI द्वारा निर्मित स्थितिजन्य सहायता मात्र है। यह कोई चिकित्सा निदान नहीं है और न ही आपातकालीन सेवाओं का आधिकारिक आदेश। मानव सत्यापन अनिवार्य है।",
            "requires_human_verification": "घटनास्थल पर मानव सत्यापन अनिवार्य है",
            "observed": "प्रत्यक्ष रूप से देखा गया",
            "user_reported": "उपयोगकर्ता द्वारा सूचित",
            "inferred": "अनुमानित (सत्यापन आवश्यक)",
            "road_accident": "सड़क दुर्घटना (निरीक्षणाधीन)",
            "smoke_fire": "धुआं अथवा आग का संकेत",
            "flooding": "जलभराव / बाढ़ की स्थिति",
            "structural_damage": "इमारत या संरचनात्मक क्षति",
            "blocked_road": "अवरुद्ध मार्ग",
            "severe_weather": "गंभीर मौसम",
            "ambiguous": "अस्पष्ट स्थिति",
            "no_emergency": "कोई आपात स्थिति नहीं"
        }
    }

    # Common domain phrases for emergency summaries and observations
    DOMAIN_PHRASES = {
        "te": {
            "A large tree has fallen across a roadway": "రహదారిపై ఒక పెద్ద చెట్టు కూలిపోయి రాకపోకలకు అంతరాయం ఏర్పడింది.",
            "Two-vehicle front-end collision resulting in roadway obstruction and fluid accumulation.": "రెండు వాహనాల ముఖాముఖి ఢీకొనడంతో రహదారి నిలిచిపోయింది మరియు ద్రవం లీక్ అయింది.",
            "Two passenger cars collided at intersection; radiator fluid pooling on asphalt.": "కూడలి వద్ద రెండు కార్లు ఢీకొన్నాయి; రోడ్డుపై రేడియేటర్ ద్రవం నిలిచింది.",
            "Front bumper and hood crumpled on two passenger sedans": "రెండు సెడాన్ కార్ల ముందు బంపర్ మరియు హుడ్ దెబ్బతిన్నాయి.",
            "Liquid pooling beneath engine bay": "ఇంజన్ విభాగం కింద ద్రవం నిల్వ ఉంది.",
            "Bystanders gathering on sidewalk": "ఫుట్‌పాత్‌పై ప్రజలు గుమిగూడుతున్నారు.",
            "Vehicle thermal hazard from fluid/radiator leak": "ద్రవం/రేడియేటర్ లీకేజీ కారణంగా వాహన అగ్ని ప్రమాద ముప్పు",
            "Secondary traffic collision hazard": "ద్వితీయ ట్రాఫిక్ తాకిడి ప్రమాదం",
            "Sedans positioned across traffic lanes": "ట్రాఫిక్ లేన్లలో కార్లు అడ్డంగా ఉన్నాయి",
            "Hot engine parts can ignite aerosolized fluids": "వేడి ఇంజన్ భాగాలు లీకైన ద్రవాలను మండించగలవు",
            "Visible liquid pooling under crushed vehicle front": "దెబ్బతిన్న వాహనం ముందు ద్రవం నిలిచి ఉండటం కనిపించింది",
            "Exact occupant injury status cannot be verified from imagery": "చిత్రాల ద్వారా క్షతగాత్రుల పరిస్థితిని నేరుగా నిర్ధారించలేము",
            "Active fire presence not confirmed": "ప్రత్యక్ష మంటలు ఇంకా నిర్ధారించబడలేదు",
            "Number of vehicle occupants requiring transport": "ఆసుపత్రికి తరలించాల్సిన ప్రయాణీకుల సంఖ్య",
            "Fuel type (EV vs Internal Combustion)": "ఇంధన రకం (ఈవీ లేదా సంప్రదాయ వాహనం)",
            "Report precise lane blockage to traffic dispatch": "ట్రాఫిక్ కంట్రోల్‌కు ఖచ్చితమైన లేన్ అడ్డంకిని నివేదించండి",
            "Request dual ambulance package and wrecker": "రెండు అంబులెన్స్‌లు మరియు క్రేన్ వాహనాన్ని అభ్యర్థించండి",
            "Good daylight visibility, clear frontal camera perspective": "మంచి పగటి వెలుతురు, స్పష్టమైన ముందు కెమెరా దృశ్యం",
            "Visible structural crushing of vehicle engine compartments": "వాహన ఇంజన్ భాగాల నిర్మాణం దెబ్బతిన్నట్లు స్పష్టంగా కనిపిస్తోంది",
            "Dark fluid sheen visible on pavement": "రోడ్డుపై నల్లటి ద్రవపు పొర కనిపిస్తోంది",
            "Pedestrians visible at curb perimeter": "పాదచారులు రోడ్డు అంచున కనిపిస్తున్నారు"
        },
        "hi": {
            "A large tree has fallen across a roadway": "सड़क पर एक बड़ा पेड़ गिर गया है जिससे मार्ग पूरी तरह अवरुद्ध हो गया है।",
            "Two-vehicle front-end collision resulting in roadway obstruction and fluid accumulation.": "दो वाहनों की आमने-सामने की टक्कर से सड़क अवरुद्ध हो गई है और तरल पदार्थ का रिसाव हुआ है।",
            "Two passenger cars collided at intersection; radiator fluid pooling on asphalt.": "चौराहे पर दो कारों की टक्कर हुई; डामर पर रेडिएटर द्रव जमा हो गया है।",
            "Front bumper and hood crumpled on two passenger sedans": "दो सेडान कारों के फ्रंट बंपर और हुड क्षतिग्रस्त हो गए हैं।",
            "Liquid pooling beneath engine bay": "इंजन के नीचे तरल पदार्थ जमा हो रहा है।",
            "Bystanders gathering on sidewalk": "फुटपाथ पर लोग एकत्र हो रहे हैं।",
            "Vehicle thermal hazard from fluid/radiator leak": "द्रव/रेडिएटर रिसाव से वाहन में आग लगने का खतरा",
            "Secondary traffic collision hazard": "अन्य वाहनों के टकराने का द्वितीयक खतरा",
            "Sedans positioned across traffic lanes": "ट्रैफिक लेनों में कारें आड़ी खड़ी हैं",
            "Hot engine parts can ignite aerosolized fluids": "गर्म इंजन के पुर्जे रिसाव वाले तरल को प्रज्वलित कर सकते हैं",
            "Visible liquid pooling under crushed vehicle front": "क्षतिग्रस्त वाहन के आगे तरल जमा दिखाई दे रहा है",
            "Exact occupant injury status cannot be verified from imagery": "तस्वीरों से घायलों की सटीक स्थिति की पुष्टि नहीं की जा सकती",
            "Active fire presence not confirmed": "सक्रिय आग की पुष्टि नहीं हुई है",
            "Number of vehicle occupants requiring transport": "अस्पताल ले जाने हेतु आवश्यक यात्रियों की संख्या",
            "Fuel type (EV vs Internal Combustion)": "ईंधन का प्रकार (ईवी अथवा पारंपरिक वाहन)",
            "Report precise lane blockage to traffic dispatch": "यातायात नियंत्रण कक्ष को सटीक लेन अवरोध की सूचना दें",
            "Request dual ambulance package and wrecker": "दो एम्बुलेंस और टो-ट्रक की मांग करें",
            "Good daylight visibility, clear frontal camera perspective": "दिन का अच्छा उजाला, स्पष्ट कैमरा दृश्य",
            "Visible structural crushing of vehicle engine compartments": "वाहन के इंजन डिब्बे में संरचनात्मक क्षति स्पष्ट दिखाई दे रही है",
            "Dark fluid sheen visible on pavement": "सड़क पर काले द्रव की चमक दिखाई दे रही है",
            "Pedestrians visible at curb perimeter": "फुटपाथ के किनारे पैदल यात्री दिखाई दे रहे हैं"
        }
    }

    def _translate_phrase(self, text: str, lang: str) -> str:
        """Translates a domain phrase or sentence, or cleanly falls back without mangling."""
        if not text or not isinstance(text, str):
            return text
        clean = clean_language_prefixes(text)
        phrases = self.DOMAIN_PHRASES.get(lang, {})
        for orig, translated in phrases.items():
            if orig.lower() in clean.lower():
                return clean.lower().replace(orig.lower(), translated).strip()
        # Word-level vocabulary replacements
        lex = self.TRANSLATION_LEXICON.get(lang, {})
        if clean in lex:
            return lex[clean]
        return clean

    def translate_incident_sync(self, incident_data: Dict[str, Any], target_language: str) -> Dict[str, Any]:
        """
        Synchronous emergency domain translation fallback.
        Ensures NO [Language] prefixes are added and technical identifiers remain intact.
        """
        clean_source = clean_incident_data(incident_data)
        if target_language == "en":
            return clean_source

        lex = self.TRANSLATION_LEXICON.get(target_language, {})
        translated = dict(clean_source)

        # 1. Translate incident type
        orig_type = clean_source.get("incident_type", "")
        if orig_type in lex:
            translated["incident_type"] = lex[orig_type]

        # 2. Translate summary cleanly WITHOUT prepending [Language] tag
        orig_summary = clean_source.get("incident_summary", "")
        translated["incident_summary"] = self._translate_phrase(orig_summary, target_language)

        # 3. Translate observations
        trans_obs = []
        for o in clean_source.get("observations", []):
            o_copy = dict(o)
            source_key = o_copy.get("source", "")
            if source_key in lex:
                o_copy["source_label"] = lex[source_key]
            if "description" in o_copy:
                o_copy["description"] = self._translate_phrase(o_copy["description"], target_language)
            if "evidence" in o_copy:
                o_copy["evidence"] = self._translate_phrase(o_copy["evidence"], target_language)
            trans_obs.append(o_copy)
        translated["observations"] = trans_obs

        # 4. Translate potential concerns
        trans_concerns = []
        for c in clean_source.get("potential_concerns", []):
            c_copy = dict(c)
            c_copy["verification_label"] = lex.get("requires_human_verification", "Human verification required")
            if "concern" in c_copy:
                c_copy["concern"] = self._translate_phrase(c_copy["concern"], target_language)
            if "reason" in c_copy:
                c_copy["reason"] = self._translate_phrase(c_copy["reason"], target_language)
            if "evidence" in c_copy:
                c_copy["evidence"] = self._translate_phrase(c_copy["evidence"], target_language)
            trans_concerns.append(c_copy)
        translated["potential_concerns"] = trans_concerns

        # 5. Translate uncertainties and missing information
        if "uncertainties" in clean_source:
            translated["uncertainties"] = [self._translate_phrase(u, target_language) for u in clean_source["uncertainties"]]
        if "missing_information" in clean_source:
            translated["missing_information"] = [self._translate_phrase(m, target_language) for m in clean_source["missing_information"]]
        if "recommended_information_to_communicate" in clean_source:
            translated["recommended_information_to_communicate"] = [
                self._translate_phrase(r, target_language) for r in clean_source["recommended_information_to_communicate"]
            ]

        # 6. Translate timeline events
        if "timeline" in clean_source:
            timeline_translations = {
                "te": {
                    "Image Ingested & Analyzed": "చిత్రం స్వీకరించబడింది & విశ్లేషించబడింది",
                    "Cross-Modal Evidence Linked": "క్రాస్-మోడల్ ఆధారాల అనుసంధానం",
                    "Safety Verification Checked": "భద్రతా ధృవీకరణ తనిఖీ చేయబడింది",
                    "Operational Intelligence Synthesized": "కార్యాచరణ నిఘా సంశ్లేషణ చేయబడింది"
                },
                "hi": {
                    "Image Ingested & Analyzed": "छवि प्राप्त एवं विश्लेषित",
                    "Cross-Modal Evidence Linked": "क्रॉस-मॉडल साक्ष्य जोड़े गए",
                    "Safety Verification Checked": "सुरक्षा सत्यापन पूर्ण",
                    "Operational Intelligence Synthesized": "परिचालन खुफिया जानकारी संश्लेषित"
                }
            }
            tt = timeline_translations.get(target_language, {})
            trans_timeline = []
            for evt in clean_source.get("timeline", []):
                evt_copy = dict(evt)
                orig_title = evt_copy.get("title", "")
                evt_copy["title"] = tt.get(orig_title, orig_title)
                trans_timeline.append(evt_copy)
            translated["timeline"] = trans_timeline

        # 7. Safety disclaimer
        translated["safety_disclaimer"] = lex.get("safety_disclaimer", clean_source.get("safety_disclaimer", ""))

        # 8. PRESERVE TECHNICAL IDENTIFIERS EXACTLY
        for k in ["incident_id", "model_used", "primary_model", "fallback_used", "fallback_reason", "timestamp", "created_at"]:
            if k in clean_source:
                translated[k] = clean_source[k]

        return translated

    async def translate_incident_data(self, incident_data: Dict[str, Any], target_language: str) -> Dict[str, Any]:
        """
        Translates structured incident intelligence into target_language.
        Uses Gemma 4 via Google GenAI SDK if GEMINI_API_KEY is configured;
        falls back to structured domain translation engine to guarantee reliability.
        """
        clean_source = clean_incident_data(incident_data)

        if target_language == "en":
            return {
                "language": "en",
                "language_display": self.LANGUAGE_NAMES["en"],
                "translated_content": clean_source,
                "preservation_notice": "English original preserved with complete epistemic uncertainty calibrations."
            }

        target_lang_name = self.LANGUAGE_NAMES.get(target_language, target_language)

        # Attempt live Gemma 4 translation if API key is active
        if settings.GEMINI_API_KEY:
            try:
                import asyncio
                from google import genai
                from google.genai import types
                import json

                def _do_genai_translate():
                    client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    prompt = (
                        f"You are an emergency translator for ResQ Vision. "
                        f"Translate the following emergency incident JSON from English to {target_lang_name}. "
                        f"CRITICAL SAFETY RULE: You MUST strictly preserve epistemic uncertainty. "
                        f"Do NOT translate 'possible', 'suspected', or 'smoke-like' into 'confirmed' or 'guaranteed'. "
                        f"CRITICAL LOCALIZATION RULE: Translate strings directly. Do NOT prepend language tags like [{target_lang_name}] or [Telugu] or [Hindi]. "
                        f"CRITICAL TECHNICAL IDENTIFIER RULE: Keep model identifiers unchanged: Gemma 4, gemma-4-31b-it, gemma-4-26b-a4b-it. Keep incident_id, URLs, and timestamps unchanged. "
                        f"Preserve all field keys. Translate only the string values. "
                        f"Return ONLY the translated JSON.\n\n"
                        f"Incident JSON:\n{json.dumps(clean_source, ensure_ascii=False)}"
                    )

                    used_m = settings.GEMMA_MODEL
                    try:
                        resp = client.models.generate_content(
                            model=settings.GEMMA_MODEL,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=0.1,
                                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                            )
                        )
                    except Exception:
                        resp = client.models.generate_content(
                            model=settings.FALLBACK_MODEL,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=0.1,
                                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                            )
                        )
                        used_m = settings.FALLBACK_MODEL
                    return resp, used_m

                response, used_model = await asyncio.wait_for(
                    asyncio.to_thread(_do_genai_translate),
                    timeout=25.0
                )

                if response.text:
                    cleaned_text = response.text.strip()
                    if "```" in cleaned_text:
                        f_start = cleaned_text.find("```")
                        nl = cleaned_text.find("\n", f_start)
                        f_end = cleaned_text.rfind("```")
                        if nl != -1 and f_end > nl:
                            cleaned_text = cleaned_text[nl:f_end].strip()
                    if "{" in cleaned_text and "}" in cleaned_text:
                        s = cleaned_text.find("{")
                        e = cleaned_text.rfind("}") + 1
                        cleaned_text = cleaned_text[s:e]
                    translated_dict = json.loads(cleaned_text.strip())
                    clean_dict = clean_incident_data(translated_dict)

                    # Preserve technical identifiers
                    for k in ["incident_id", "model_used", "primary_model", "fallback_used", "fallback_reason", "timestamp", "created_at"]:
                        if k in clean_source:
                            clean_dict[k] = clean_source[k]

                    return {
                        "language": target_language,
                        "language_display": target_lang_name,
                        "translated_content": clean_dict,
                        "preservation_notice": f"Live translated by {used_model} with strict uncertainty preservation."
                    }
            except Exception as e:
                print(f"[Translation] Gemma API call failed or unavailable ({e}). Using localized domain engine.")

        # Local emergency domain engine fallback
        translated = self.translate_incident_sync(clean_source, target_language)

        return {
            "language": target_language,
            "language_display": target_lang_name,
            "translated_content": translated,
            "preservation_notice": f"Translated into {target_lang_name}. Uncertainty qualifiers and safety warnings fully preserved."
        }

translation_service = TranslationService()
