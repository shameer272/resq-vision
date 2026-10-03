# Gemma 4 Integration Guide

ResQ Vision is powered by Google's **Gemma 4** open-model family, accessed through the official Google GenAI SDK (`google-genai`).

## 1. Official Model Identifiers

ResQ Vision supports and validates the official model identifiers:
- **Primary Model**: `gemma-4-31b-it` (31B Dense Multimodal Instruction-Tuned Model)
- **Fallback / Edge Model**: `gemma-4-26b-a4b-it` (26B Mixture-of-Experts with 3.8B active parameters)

The model is configured via the environment variable `GEMMA_MODEL` in `.env`:
```env
GEMMA_MODEL=gemma-4-31b-it
FALLBACK_MODEL=gemma-4-26b-a4b-it
```

## 2. Official Google GenAI SDK Setup

ResQ Vision utilizes the unified `google-genai` Python library:

```python
from google import genai
from google.genai import types

# Server-side initialization
client = genai.Client(api_key=settings.GEMINI_API_KEY)
```

Official documentation references:
- [Google GenAI Python SDK](https://ai.google.dev/gemini-api/docs/get-started)
- [Function Calling in GenAI](https://ai.google.dev/gemini-api/docs/function-calling)
- [Structured Outputs in GenAI](https://ai.google.dev/gemini-api/docs/interactions-overview)

## 3. Multimodal Analysis Pattern

ResQ Vision supports single and multi-image reasoning (up to 4 scene angles) together with audio transcripts, text descriptions, and RAG knowledge citations.

```python
# Converting raw uploaded bytes to SDK Image Parts
image_parts = [
    types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
    for img_bytes, mime_type in images
]

# Configuring typed JSON structured response
config = types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    temperature=0.2,
    response_mime_type="application/json"
)

response = client.models.generate_content(
    model=settings.GEMMA_MODEL,
    contents=image_parts + [text_prompt],
    config=config
)
```

## 4. Self-Correcting Schema Repair

If the model response contains formatting anomalies or JSON truncation:
1. Pydantic parser catches the `ValidationError`.
2. Backend automatically fires a targeted repair prompt back to Gemma 4 specifying the missing attributes.
3. Repaired JSON is re-validated before passing into the safety filtering layer.
4. Client never receives a raw error or crash.

## 5. Epistemic Uncertainty Preservation

When translating into regional languages (Telugu and Hindi), Gemma 4 is prompted with strict epistemic calibration constraints:
- Words like "suspected", "possible", or "smoke-like plume" must **never** be translated into deterministic words like "confirmed" or "guaranteed".
- Every potential hazard requires explicit on-scene verification badges.
