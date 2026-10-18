"""Neuro-SAN adapter; deterministic rules are independently testable."""
import asyncio
import json
from neuro_san.interfaces.coded_tool import CodedTool
from coded_tools.campusfix.campusfix_rules import resolve_location, _classify, _duplicate, _assign, _verify, assess


class CampusFixTool(CodedTool):
    async def async_invoke(self, args, sly_data):
        args = args or {}
        # These host-owned fields are deliberately absent from LLM function parameters.
        confirmation = (sly_data or {}).get("campusfix_confirmation")
        conflict = (sly_data or {}).get("campusfix_source_conflict", "")
        action = args.get("action")
        complaint, location = str(args.get("complaint", "")), str(args.get("location_text", ""))
        def run():
            if action == "resolve_location":
                return resolve_location(location, confirmation, conflict)
            if action == "triage":
                return _classify(complaint)
            if action == "duplicate":
                return _duplicate(complaint, location)
            if action in {"assign", "report", "assess", "verify"}:
                result = assess(complaint, location, confirmation, conflict)
                # Information requests intentionally have no complaint assignment.
                # Return a safe non-error result instead of indexing a missing key.
                if action == "assign":
                    if result.get("intent") == "information":
                        return {
                            "assignment_target_type": "NONE",
                            "assignment_target_role": None,
                            "assignment_target_roles": [],
                            "assignment_status": "NOT_APPLICABLE",
                            "assignment_rationale": "Information requests are answered directly and are not routed as complaints.",
                            "approval_required": False,
                            "next_action": result.get("answer", "Answer the location question directly."),
                        }
                    return result.get("assignment", {
                        "assignment_status": "TOOL_ERROR",
                        "error": "Assessment did not return an assignment object."
                    })
                if action == "verify":
                    assignment = result.get("assignment")
                    if not isinstance(assignment, dict):
                        return {
                            "valid": False,
                            "reason": "No assignment proposal exists for an information request.",
                            "approval_required": False,
                        }
                    return _verify(assignment, str(args.get("assignment_target_role", "")))
                if action == "report":
                    # Compact the report handoff so the frontman does not have to
                    # interpret the entire nested assessment JSON before replying.
                    if result.get("intent") == "information":
                        return {
                            "intent": "information",
                            "answer": result.get("answer") or result.get("report")
                                      or "I couldn't identify that location. Please provide a building or room code.",
                        }
                    return {
                        "intent": result.get("intent", "complaint"),
                        "report": result.get("report")
                                  or result.get("next_action")
                                  or "The assessment completed, but no report summary was generated.",
                        "workflow_status": result.get("workflow_status", "ASSESSMENT_ONLY"),
                        "persisted": bool(result.get("persisted", False)),
                    }
                return result
            return {"error": f"Unknown CampusFix action: {action}", "workflow_status": "TOOL_ERROR"}
        try:
            result = await asyncio.to_thread(run)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result = {"error": str(exc), "workflow_status": "TOOL_ERROR",
                      "next_action": "Project owner must repair data or tool configuration before finalizing intake."}
        return json.dumps(result, ensure_ascii=False)
