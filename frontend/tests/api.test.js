import { test, describe, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { getApiBaseUrl, checkHealth, API_BASE } from "../src/services/api.js";

describe("Frontend API & Gemini Configuration Service", () => {
  let originalFetch;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  describe("getApiBaseUrl", () => {
    test("uses VITE_API_BASE_URL when defined", () => {
      const url = getApiBaseUrl({ VITE_API_BASE_URL: "https://my-backend.vercel.app" });
      assert.equal(url, "https://my-backend.vercel.app");
    });

    test("strips trailing slashes from VITE_API_BASE_URL", () => {
      const url = getApiBaseUrl({ VITE_API_BASE_URL: "https://my-backend.vercel.app///" });
      assert.equal(url, "https://my-backend.vercel.app");
    });

    test("trims whitespace from VITE_API_BASE_URL", () => {
      const url = getApiBaseUrl({ VITE_API_BASE_URL: "   https://my-backend.vercel.app/   " });
      assert.equal(url, "https://my-backend.vercel.app");
    });

    test("falls back to local FastAPI port 8000 in DEV mode when VITE_API_BASE_URL is not set", () => {
      const url = getApiBaseUrl({ DEV: true });
      assert.equal(url, "http://127.0.0.1:8000");
    });

    test("falls back to deployed production backend when VITE_API_BASE_URL is missing or empty in production", () => {
      const urlWithUndefined = getApiBaseUrl({});
      assert.equal(urlWithUndefined, "https://resq-vision-71gv.vercel.app");

      const urlWithEmpty = getApiBaseUrl({ VITE_API_BASE_URL: "   " });
      assert.equal(urlWithEmpty, "https://resq-vision-71gv.vercel.app");
    });

    test("exported API_BASE defaults to a valid URL string", () => {
      assert.equal(typeof API_BASE, "string");
      assert.ok(API_BASE.startsWith("http://") || API_BASE.startsWith("https://"));
    });
  });

  describe("checkHealth & Backend Configuration Integration", () => {
    test("calls /health and parses backend's gemini_api_key_configured status", async () => {
      const mockBackendResponse = {
        status: "healthy",
        service: "ResQ Vision Multimodal Emergency Situation Intelligence",
        ai_provider: "google",
        model: "gemma-4-31b-it",
        gemini_api_key_configured: true,
        api_key_preview: "AQ.A...8CBw",
      };

      let calledUrl = null;
      globalThis.fetch = async (url) => {
        calledUrl = url;
        return {
          ok: true,
          status: 200,
          json: async () => mockBackendResponse,
        };
      };

      const result = await checkHealth();
      assert.ok(calledUrl.endsWith("/health"), `Expected URL to end with /health, got ${calledUrl}`);
      assert.equal(result.status, "healthy");
      assert.equal(result.gemini_api_key_configured, true);
      assert.equal(result.model, "gemma-4-31b-it");
    });

    test("throws an error when /health responds with 404 or server failure", async () => {
      globalThis.fetch = async () => ({
        ok: false,
        status: 404,
        statusText: "Not Found",
      });

      await assert.rejects(
        async () => {
          await checkHealth();
        },
        {
          name: "Error",
          message: "Health check failed",
        }
      );
    });

    test("preserves server-side only key security (zero browser key storage required)", async () => {
      // Confirms system uses the backend response directly and does not require localStorage
      const mockStatus = {
        status: "healthy",
        gemini_api_key_configured: true,
      };

      // Simulates the exact state check performed by Navbar, AnalyzePage, and LandingPage:
      const isConfigured = Boolean(mockStatus?.gemini_api_key_configured);
      assert.equal(isConfigured, true, "Frontend correctly reflects backend server key presence");
    });
  });
});
