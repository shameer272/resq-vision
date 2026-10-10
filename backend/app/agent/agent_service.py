import json
from typing import Dict, Any, List, Optional, Callable, TypedDict
from app.core.config import settings
from app.tools.incident_tools import incident_tools

class ToolDefinition(TypedDict):
    fn: Callable[..., Any]
    description: str

class AgentService:
    """
    Agent Orchestration Layer for ResQ Vision.
    Manages structured tool execution, function calling dispatch,
    and multi-step reasoning cycles adhering to official Google GenAI standards.

    Workflow:
    MODEL REQUESTS TOOL -> BACKEND EXECUTES TOOL -> TOOL RESULT RETURNS TO MODEL -> FINAL STRUCTURED RESPONSE
    """

    AVAILABLE_TOOLS: Dict[str, ToolDefinition] = {
        "generate_incident_report": {
            "fn": incident_tools.generate_incident_report,
            "description": "Synthesizes structured incident data into an official METHANE operational report."
        },
        "generate_responder_checklist": {
            "fn": incident_tools.generate_responder_checklist,
            "description": "Generates a triage verification checklist for first responders."
        },
        "get_location_context": {
            "fn": incident_tools.get_location_context,
            "description": "Provides regional geographic, jurisdictional, and hospital facility context for a given location."
        },
        "retrieve_safety_guidance": {
            "fn": incident_tools.retrieve_safety_guidance,
            "description": "Retrieves verified public safety references from the local RAG knowledge base."
        },
        "translate_report": {
            "fn": incident_tools.translate_report,
            "description": "Translates incident report into Telugu or Hindi while preserving epistemic uncertainty."
        },
        "save_incident": {
            "fn": incident_tools.save_incident,
            "description": "Persists an incident report to MongoDB or local storage."
        },
        "export_report": {
            "fn": incident_tools.export_report,
            "description": "Compiles and exports the incident report as a PDF document."
        },
        "validate_incident_inputs": {
            "fn": incident_tools.validate_incident_inputs,
            "description": "Validates incoming emergency report completeness, image count, and payload limits."
        },
        "classify_incident_support": {
            "fn": incident_tools.classify_incident_support,
            "description": "Provides classification support and keyword cue matching across emergency categories."
        },
        "manage_incident_history": {
            "fn": incident_tools.manage_incident_history,
            "description": "Lists, retrieves, and inspects saved incident records from persistent storage."
        }
    }


    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Safely executes a registered tool from the allowlist with structured validation.
        """
        if tool_name not in self.AVAILABLE_TOOLS:
            return {
                "error": f"Tool '{tool_name}' is not in the safe allowlist.",
                "allowed_tools": list(self.AVAILABLE_TOOLS.keys())
            }

        tool_meta = self.AVAILABLE_TOOLS[tool_name]
        fn = tool_meta["fn"]

        if not callable(fn):
            return {
                "status": "error",
                "tool": tool_name,
                "error_message": f"Tool '{tool_name}' handler is not callable."
            }

        try:
            result = fn(**arguments)
            return {
                "status": "success",
                "tool": tool_name,
                "output": result
            }
        except Exception as e:
            return {
                "status": "error",
                "tool": tool_name,
                "error_message": str(e)
            }

    async def run_model_tool_cycle(
        self,
        prompt: str,
        tools_to_enable: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes an end-to-end model-driven function calling cycle:
        1. Model receives prompt and tool declarations.
        2. Model requests tool invocation (function_call).
        3. Backend executes registered function securely.
        4. Tool result is passed back to model (function_response).
        5. Model synthesizes final response incorporating tool results.
        """
        execution_trace = []
        
        # Check if live Gemini API is configured
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                
                # Expose specific tools as callable Python functions
                def tool_get_location(location_query: str) -> str:
                    """Gets geographic and hospital context for an emergency location."""
                    return json.dumps(incident_tools.get_location_context(location_query))

                def tool_retrieve_guidance(query: str, incident_type: str = "general") -> str:
                    """Retrieves official safety protocols from the curated knowledge base."""
                    return json.dumps(incident_tools.retrieve_safety_guidance(query, incident_type))

                # Step 1: Initial call with tools
                config = types.GenerateContentConfig(
                    tools=[tool_get_location, tool_retrieve_guidance],
                    temperature=0.1
                )
                
                execution_trace.append({
                    "step": "Model Prompting",
                    "detail": "Sending prompt and tool schemas to Gemma 4"
                })

                response = client.models.generate_content(
                    model=settings.GEMMA_MODEL,
                    contents=prompt,
                    config=config
                )

                # Step 2 & 3: Check for function calls
                if hasattr(response, "function_calls") and response.function_calls and response.candidates and len(response.candidates) > 0 and response.candidates[0].content is not None:
                    contents_history: list[types.ContentUnionDict] = [
                        types.Content(role="user", parts=[types.Part.from_text(text=prompt)]),
                        response.candidates[0].content
                    ]
                    func_response_parts: list[types.Part] = []
                    for call in response.function_calls:
                        tool_name = call.name or ""
                        tool_args = dict(call.args) if call.args else {}
                        execution_trace.append({
                            "step": "MODEL REQUESTS TOOL",
                            "tool": tool_name,
                            "args": tool_args
                        })
                        
                        # Backend executes tool
                        if "location" in tool_name:
                            tool_result = incident_tools.get_location_context(tool_args.get("location_query", ""))
                        else:
                            tool_result = incident_tools.retrieve_safety_guidance(tool_args.get("query", ""))
                        
                        execution_trace.append({
                            "step": "BACKEND EXECUTES TOOL",
                            "tool": tool_name,
                            "status": "success"
                        })

                        # Return tool result to model
                        func_response_part = types.Part.from_function_response(
                            name=tool_name,
                            response={"result": tool_result}
                        )
                        func_response_parts.append(func_response_part)
                        execution_trace.append({
                            "step": "TOOL RESULT RETURNS TO MODEL",
                            "tool": tool_name
                        })

                    contents_history.append(types.Content(role="user", parts=func_response_parts))

                    # Step 4: Final response from model
                    final_res = client.models.generate_content(
                        model=settings.GEMMA_MODEL,
                        contents=contents_history
                    )
                    execution_trace.append({
                        "step": "FINAL STRUCTURED RESPONSE",
                        "detail": "Gemma 4 synthesized final operational assessment with tool findings"
                    })

                    return {
                        "mode": "live_gemma_function_calling",
                        "final_text": final_res.text,
                        "execution_trace": execution_trace
                    }
            except Exception as e:
                execution_trace.append({
                    "step": "Fallback",
                    "detail": f"Live tool cycle encountered API condition ({e}); proceeding with local verified pipeline"
                })

        return {
            "mode": "local_orchestration",
            "execution_trace": execution_trace
        }

    async def run_agentic_workflow(
        self,
        incident_data: Dict[str, Any],
        requested_goals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Orchestrates an agentic multi-tool response sequence across the 7 verified tools:
        1. Contextual location resolution (get_location_context)
        2. Safety guidance retrieval (retrieve_safety_guidance)
        3. Responder triage checklist synthesis (generate_responder_checklist)
        4. Official METHANE report compilation (generate_incident_report)
        5. Translation if requested (translate_report)
        6. Incident persistence (save_incident)
        7. PDF compilation (export_report)
        """
        goals = requested_goals or ["location_context", "safety_guidance", "checklist", "report", "save"]
        execution_trace = []

        results = {
            "incident_id": incident_data.get("incident_id"),
            "tool_outputs": {}
        }

        # Step 1: Location Context Tool
        if "location_context" in goals and incident_data.get("location"):
            tool_res = self.execute_tool("get_location_context", {"location_query": incident_data["location"]})
            results["tool_outputs"]["location_context"] = tool_res.get("output")
            execution_trace.append({
                "step": "BACKEND EXECUTES TOOL",
                "tool": "get_location_context",
                "status": tool_res.get("status"),
                "reason": "Acquired regional emergency jurisdiction and terrain info"
            })

        # Step 2: Safety Guidance via RAG Tool
        if "safety_guidance" in goals:
            query = incident_data.get("incident_summary", incident_data.get("incident_type", "incident"))
            tool_res = self.execute_tool("retrieve_safety_guidance", {
                "query": query,
                "incident_type": incident_data.get("incident_type")
            })
            results["tool_outputs"]["safety_guidance"] = tool_res.get("output")
            execution_trace.append({
                "step": "BACKEND EXECUTES TOOL",
                "tool": "retrieve_safety_guidance",
                "status": tool_res.get("status"),
                "reason": "Retrieved verified public safety citations"
            })

        # Step 3: Responder Checklist Tool
        if "checklist" in goals:
            tool_res = self.execute_tool("generate_responder_checklist", {"incident_data": incident_data})
            results["tool_outputs"]["checklist"] = tool_res.get("output")
            execution_trace.append({
                "step": "BACKEND EXECUTES TOOL",
                "tool": "generate_responder_checklist",
                "status": tool_res.get("status"),
                "reason": "Generated responder information verification checklist"
            })

        # Step 4: Incident Report Tool
        if "report" in goals:
            tool_res = self.execute_tool("generate_incident_report", {"incident_data": incident_data})
            results["tool_outputs"]["report"] = tool_res.get("output")
            execution_trace.append({
                "step": "BACKEND EXECUTES TOOL",
                "tool": "generate_incident_report",
                "status": tool_res.get("status"),
                "reason": "Compiled operational METHANE report"
            })

        # Step 5: Translate Report Tool (if target language requested)
        if "translate" in goals:
            target_lang = incident_data.get("language", "te")
            tool_res = self.execute_tool("translate_report", {
                "incident_data": incident_data,
                "target_language": target_lang
            })
            results["tool_outputs"]["translation"] = tool_res.get("output")
            execution_trace.append({
                "step": "BACKEND EXECUTES TOOL",
                "tool": "translate_report",
                "status": tool_res.get("status"),
                "reason": f"Translated into {target_lang} with preserved uncertainty"
            })

        # Step 6: Save Incident Tool
        if "save" in goals:
            tool_res = self.execute_tool("save_incident", {"incident_data": incident_data})
            results["tool_outputs"]["save"] = tool_res.get("output")
            execution_trace.append({
                "step": "BACKEND EXECUTES TOOL",
                "tool": "save_incident",
                "status": tool_res.get("status"),
                "reason": "Persisted intelligence record to system storage"
            })

        # Step 7: Export Report Tool (if requested)
        if "export" in goals:
            tool_res = self.execute_tool("export_report", {
                "report_data": incident_data,
                "format_type": "pdf"
            })
            results["tool_outputs"]["export"] = tool_res.get("output")
            execution_trace.append({
                "step": "BACKEND EXECUTES TOOL",
                "tool": "export_report",
                "status": tool_res.get("status"),
                "reason": "Compiled high-contrast PDF document"
            })

        results["execution_trace"] = execution_trace
        return results

agent_service = AgentService()
