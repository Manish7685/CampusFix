"""Deterministic CampusFix intent handling, intake, and council-routing proposals."""
from __future__ import annotations
import json
import os
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROLES = (
    "HSS1 — Hostel and Safety Secretary 1 (Boys)",
    "HSS2 — Hostel and Safety Secretary 2 (Girls)",
    "Sports Secretary", "General Secretary 1 (Boys)",
    "General Secretary 2 (Girls)", "Academic Secretary", "Mess Secretary",
)


def _normalize(text):
    text = unicodedata.normalize("NFKD", (text or "").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def _load_data(name, env):
    # Explicit bad paths fail closed rather than silently using different data.
    path = Path(os.environ[env]) if os.environ.get(env) else ROOT / "data" / name
    with path.open(encoding="utf-8") as source:
        value = json.load(source)
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object in {path.name}")
    return value


def _load_knowledge():
    return _load_data("campus_knowledge.json", "CAMPUSFIX_KNOWLEDGE_PATH")


def _all_locations(knowledge):
    result = [dict(item) for item in knowledge["locations"]]
    # Hostel room codes use <block><floor digit><two-digit room>, e.g. B205.
    # Resolve parent buildings from the knowledge base rather than inventing location IDs.
    for code in ("A", "B", "C"):
        parent = next((loc for loc in knowledge["locations"]
                       if _normalize(loc.get("name", "")) == f"{code.lower()} block hostel"
                       or any(_normalize(alias) == f"{code} block" for alias in loc.get("aliases", []))), None)
        if parent:
            for floor in range(1, int(parent.get("floors", 4)) + 1):
                for room in range(1, 100):
                    room_code = f"{code}{floor}{room:02d}"
                    result.append({"id": "CODE-" + room_code, "name": room_code,
                                   "aliases": [f"Room {room_code}"], "status": "user-confirmed",
                                   "parent": parent["id"],
                                   "details": [f"{parent['name']}, floor {floor}, room {room:02d}"]})
    # Academic Block room codes: one computer lab and five lecture halls/classrooms per floor.
    academic = next((loc for loc in knowledge["locations"] if loc.get("id") == "ACADEMIC-BLOCK"), None)
    if academic:
        for floor in range(1, min(int(academic.get("floors", 3)), 3) + 1):
            result.append({"id": f"CODE-CL{floor}01", "name": f"CL{floor}01",
                           "aliases": [f"Computer Lab {floor}"], "status": "user-confirmed",
                           "parent": academic["id"],
                           "details": [f"Academic Block, floor {floor}, Computer Lab 01"]})
            for room in range(1, 6):
                code_value = f"LH{floor}{room:02d}"
                result.append({"id": "CODE-" + code_value, "name": code_value,
                               "aliases": [f"Lecture Hall {floor} room {room:02d}"],
                               "status": "user-provided-example", "parent": academic["id"],
                               "details": [f"Academic Block, floor {floor}, Lecture Hall {room:02d}"]})
    for item in knowledge.get("room_code_examples", []):
        parents = [loc["id"] for loc in knowledge["locations"] if item.get("type") == loc["name"] or
                   any(_contains(_normalize(item.get("meaning", "")), term) for term in [loc["name"], *loc.get("aliases", [])])]
        result.append({"id": "CODE-" + item["code"].upper(), "name": item["code"].upper(),
                       "aliases": [item.get("meaning", "")], "status": item.get("status"),
                       "parent": parents[0] if len(parents) == 1 else None,
                       "details": [item.get("meaning", "")]})
    return result


def _contains(text, phrase):
    phrase = _normalize(phrase)
    return bool(phrase and re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text))


def _location_answer(text, candidates):
    """Return a concise answer for a direct, known-location question."""
    norm = _normalize(text)
    if not (norm.startswith(("where is ", "where s ", "where are ", "what is ", "what s ", "tell me about ", "locate "))):
        return None
    if not candidates:
        return "I couldn't identify that location in the current campus knowledge. What building or room code do you mean?"
    chosen = candidates[0]
    code = chosen["canonical_name"]
    # Hostel room codes use <block><floor digit><two-digit room number>.
    room_match = re.fullmatch(r"([ABC])(\d)(\d{2})", code.upper())
    if room_match:
        block, floor_text, room_text = room_match.groups()
        floor = int(floor_text)
        ordinal = {1: "1st", 2: "2nd", 3: "3rd"}.get(floor, f"{floor}th")
        return f"Room {code.upper()} is in {block} Block Hostel, on the {ordinal} floor, room {room_text}."
    academic_match = re.fullmatch(r"(CL|LH)([123])(\d{2})", code.upper())
    if academic_match:
        prefix, floor_text, room_text = academic_match.groups()
        floor_label = {"1": "1st", "2": "2nd", "3": "3rd"}[floor_text]
        room_num = int(room_text)
        kind = "Computer Lab" if prefix == "CL" else "Lecture Hall"
        return f"{code.upper()} is {kind} {room_num:02d} on the {floor_label} floor of the Academic Block."
    knowledge = _load_knowledge()
    item = next((row for row in knowledge.get("room_code_examples", []) if row["code"].upper() == code.upper()), None)
    if item:
        meaning = item.get("meaning", "")
        m = re.search(r"floor (\d+), (?:lab|room) (\d+)", meaning, re.I)
        if m:
            floor_num = int(m.group(1))
            floor_label = {1: "1st", 2: "2nd", 3: "3rd"}.get(floor_num, f"{floor_num}th")
            room_num = int(m.group(2))
            if code.upper().startswith("CL"):
                return f"{code.upper()} is Computer Lab {room_num:02d} on the {floor_label} floor of the Academic Block."
            if code.upper().startswith("LH"):
                return f"{code.upper()} is Lecture Hall {room_num:02d} on the {floor_label} floor of the Academic Block."
        return f"{code.upper()} means {meaning}."
    loc = next((row for row in knowledge.get("locations", []) if row["id"] == chosen["location_id"]), None)
    if loc:
        details = loc.get("details", [])
        useful = details[0] if details else ""
        return f"{loc['name']}." + (f" {useful}." if useful else "")
    return f"{code} is listed in the campus knowledge base."


def resolve_location(text, confirmation=None, source_conflict=""):
    norm = _normalize(text)
    knowledge = _load_knowledge()
    candidates = []
    for item in _all_locations(knowledge):
        matched = [term for term in [item["name"], *item.get("aliases", [])]
                   if _normalize(term) and _contains(norm, term)]
        if matched:
            candidates.append({"location_id": item["id"], "canonical_name": item["name"],
                               "knowledge_status": item.get("status"), "matched_terms": matched,
                               "parent": item.get("parent"),
                               "match_method": "normalized_whole_phrase"})
    # An explicit code and its documented parent are one location, not competing choices.
    parents = {c["parent"] for c in candidates if c.get("parent")}
    candidates = [c for c in candidates if c["location_id"] not in parents]
    # The same documented code can be generated from the general format and listed as an example.
    unique = {}
    for candidate in candidates:
        unique.setdefault(candidate["location_id"], candidate)
    candidates = list(unique.values())
    status, selected = "UNVERIFIED", None
    question = "Which known building or room is affected?"
    if len(candidates) == 1:
        selected = candidates[0]
        known_status = str(selected.get("knowledge_status", "")).lower()
        if known_status.startswith("user-confirmed") or known_status in {"user-provided", "user-provided-example"}:
            status, question = "KNOWN_LOCATION", None
        else:
            status, question = "CANDIDATE_NEEDS_USER_CONFIRMATION", f"Did you mean {selected['canonical_name']}?"
    elif len(candidates) > 1:
        status = "AMBIGUOUS"
        question = "Which location do you mean: " + ", ".join(c["canonical_name"] for c in candidates) + "?"
    elif _contains(norm, "computer lab"):
        question = "Which computer lab is affected: CL101, CL201, CL301, or another location?"
    bound = isinstance(confirmation, dict) and confirmation.get("original_location_text") == text
    if bound and confirmation.get("confirmed") is True:
        chosen = next((c for c in candidates if c["location_id"] == confirmation.get("location_id")), None)
        if chosen:
            selected, status, question = chosen, "CONFIRMED_BY_REPORTER", None
    broad = any(_contains(norm, p) for p in ("any washroom", "all washrooms", "everywhere", "campus wide", "across campus"))
    scope_confirmed = bound and confirmation.get("scope_confirmed") is True
    if broad and not scope_confirmed:
        question = "Is the problem campus-wide, or which buildings or floors are affected?"
    if source_conflict:
        status = "SOURCE_CONFLICT"
        question = "The location sources disagree. Which reported location is correct?"
    detail_discrepancy = None
    if selected:
        canonical_id = selected.get("parent") or selected["location_id"]
        known = next((item for item in knowledge["locations"] if item["id"] == canonical_id), {})
        floor_match = re.search(r"\b(\d+)(?:st|nd|rd|th)? floor\b", norm)
        bad_floor = floor_match and known.get("floors") and not 1 <= int(floor_match[1]) <= known["floors"]
        bad_ground = canonical_id == "ACADEMIC-BLOCK" and _contains(norm, "ground floor")
        if bad_floor or bad_ground:
            detail_discrepancy = "Reported floor conflicts with the campus knowledge base."
            status = "SOURCE_CONFLICT"
            question = f"The floor reported for {known['name']} conflicts with the campus knowledge base. Which floor do you mean?"
    direct_answer = _location_answer(text, candidates) if selected else None
    return {"original_location_text": text, "location_status": status,
            "canonical_location": selected["canonical_name"] if selected else None,
            "location_id": selected["location_id"] if selected else None,
            "verified": status in {"KNOWN_LOCATION", "CONFIRMED_BY_REPORTER"}, "candidates": candidates,
            "direct_answer": direct_answer,
            "reported_detail": text,
            "detail_verification": "Only the matched candidate is resolved; other floor, room and landmark details remain reported text.",
            "scope_status": "NEEDS_CLARIFICATION" if broad and not scope_confirmed else "AS_REPORTED",
            "source_discrepancy": source_conflict or detail_discrepancy, "question": question}


def _classify(complaint):
    text = _normalize(complaint)
    groups = {
        "network": ("wifi", "wi fi", "network", "internet", "router"),
        "electrical": ("power", "electric", "electrical", "sparking", "sparks", "short circuit", "lights", "light", "wiring", "socket"),
        "plumbing": ("leak", "leaking", "water supply", "no water", "pipe", "sink", "tap", "flood", "flooding"),
    }
    evidence = {key: [term for term in terms if _contains(text, term)] for key, terms in groups.items()}
    kinds = [key for key, terms in evidence.items() if terms]
    issue = kinds[0] if kinds else "other"
    hazards = [term for term in ("sparking", "sparks", "short circuit", "smoke", "fire", "burning smell", "electric shock", "exposed live wire", "gas smell", "trapped", "collapse", "blocked exit", "injury")
               if _contains(text, term) and not any(_contains(text, p + term) for p in ("no ", "no visible ", "without ", "not "))]
    water_electric = bool(evidence["electrical"]) and any(_contains(text, p) for p in ("leak", "leaking", "flood", "flooding"))
    priority, rationale = "normal", "No explicit urgency trigger identified by the documented keyword rules."
    questions, escalation = [], None
    if hazards or water_electric:
        priority = "critical"
        rationale = "Reported hazard indicators: " + ", ".join(hazards or ["water leak/flood and electrical equipment mentioned together; proximity requires confirmation"]) + "."
        escalation = "Notify the appropriate campus authority immediately; keep clear of the suspected hazard and do not wait for automated intake."
        if water_electric:
            questions.append("Is the water reaching electrical equipment or an occupied area?")
    elif any(_contains(text, p) for p in ("flood", "flooding", "all washrooms", "any washroom")):
        priority, rationale = "high", "Reported flooding or widespread loss of service needs human review."
    elif any(_contains(text, p) for p in ("leak", "leaking")):
        if any(_contains(text, p) for p in ("small drip", "minor drip", "contained")):
            priority, rationale = "medium", "Reporter describes a small or contained leak; no immediate hazard indicator identified."
        else:
            priority, rationale = "high", "Leak severity is unknown; retain elevated priority pending a safety assessment."
            questions.append("Is the leak contained, spreading, or near electrical equipment or people?")
    elif issue != "other":
        priority, rationale = "medium", "Reported service or equipment fault without an explicit immediate hazard indicator."
        if _contains(text, "power backup"):
            questions.append("Does the backup failure affect safety equipment or essential services?")
    known_location_terms = (
        "block a", "block b", "block c", "hostel", "academic block", "admin block",
        "tnp block", "computer lab", "classroom", "floor", "room", "gate", "mess",
        "canteen", "auditorium", "plaza", "cl101", "cl201", "cl301", "b201", "b104", "c306",
    )
    needs_location_confirmation = not any(_contains(text, term) for term in known_location_terms)
    return {"issue_type": issue, "issue_types": kinds or ["other"], "classification_evidence": evidence,
            "classification_method": "deterministic_keyword_rules; not a diagnosis", "priority": priority,
            "priority_rationale": rationale, "approval_required": priority in {"high", "critical"},
            "escalation": escalation, "questions": questions,
            "needs_location_confirmation": needs_location_confirmation,
            "uncertainty": "Keyword rules cannot establish on-site conditions; humans must assess unrecognized or disputed hazards."}


def _duplicate(complaint, location_text="", records=None):
    if records is not None:
        dataset = records
    elif os.environ.get("CAMPUSFIX_RECORDS_PATH"):
        # An explicitly configured missing/bad path should still fail visibly.
        dataset = _load_data("demo_work_orders.json", "CAMPUSFIX_RECORDS_PATH")
    else:
        # The optional local demo fixture may not be installed in every project copy.
        # Missing fixture means zero local records checked, not a failed complaint intake.
        try:
            dataset = _load_data("demo_work_orders.json", "CAMPUSFIX_RECORDS_PATH")
        except FileNotFoundError:
            dataset = {"source": "local demo fixture unavailable", "synthetic": True, "records": []}
    ids = {c["location_id"] for c in resolve_location(location_text)["candidates"]}
    issue = _classify(complaint)["issue_type"]
    stop = {"the", "a", "an", "in", "at", "near", "on", "is", "of", "and", "to"}
    words = set(_normalize(complaint).split()) - stop
    checked, matches = [], []
    for row in dataset["records"]:
        existing = set(_normalize(row["description"]).split()) - stop
        similarity = len(words & existing) / max(1, len(words | existing))
        same_location, same_type = row.get("location_id") in ids, row.get("issue_type") == issue
        candidate = row.get("status") == "open" and same_location and same_type and similarity >= 0.25
        reason = f"Location candidate overlap={same_location}; issue type matches={same_type}; token Jaccard={similarity:.3f}; status={row.get('status')}."
        checked.append({"record_id": row["id"], "similarity": round(similarity, 3),
                        "decision": "POSSIBLE_DUPLICATE" if candidate else "NO_MATCH", "rationale": reason})
        if candidate:
            matches.append({**row, "similarity": round(similarity, 3), "rationale": reason, "requires_human_confirmation": True})
    return {"matches": matches, "records_checked": checked, "records_checked_count": len(checked),
            "source": dataset["source"], "synthetic": dataset.get("synthetic", True),
            "decision": "POSSIBLE_DUPLICATE" if matches else "NO_MATCH_IN_RECORDS_CHECKED",
            "note": "Only the listed local records were checked. Location matches may be unconfirmed. No auto-merge or live database query occurred.",
            "similarity_method": "Normalized token Jaccard excluding fixed stop words; threshold 0.25 plus location, type and open status"}


def _assign(issue_type, location=None, triage=None, routing=None):
    """Build a routing proposal from the owner-approved CampusFix policy."""
    location = location or {"location_status": "UNVERIFIED", "verified": False}
    triage = triage or {"approval_required": True, "priority": "normal"}
    routing = routing if routing is not None else _load_data("student_council_routing.json", "CAMPUSFIX_ROUTING_PATH")
    result = {"assignment_target_type": "STUDENT_COUNCIL_MEMBER", "assignment_target_role": None,
              "assignment_target_roles": [], "assignment_status": "PENDING_ROUTING_REVIEW",
              "assignment_rationale": "No approved routing rule supports this complaint.",
              "location_verification_status": location.get("location_status", "UNVERIFIED"),
              "approval_required": bool(triage.get("approval_required", True)),
              "next_action": "Project owner must review the routing proposal."}
    rules = routing.get("rules", [])
    for rule in rules:
        roles = rule.get("roles") or ([rule["role"]] if rule.get("role") else [])
        if any(role not in ROLES for role in roles):
            raise ValueError("Routing role is outside the council-role allowlist")
        if not rule.get("location_ids") or not rule.get("issue_types") or not rule.get("responsibility_evidence"):
            raise ValueError("Routing requires location_ids, issue_types and responsibility_evidence")
    if routing.get("owner_approved") is not True:
        result["approval_required"] = True
        return result

    original = str(location.get("original_location_text", ""))
    text = _normalize(original + " " + str(location.get("canonical_location", "")))
    issue = _normalize(issue_type)
    priority = _normalize(triage.get("priority", "normal"))
    location_id = location.get("location_id")
    route_location_ids = {location_id} if location_id else set()
    if str(location_id or "").startswith("CODE-"):
        code = str(location_id)[5:]
        knowledge = _load_knowledge()
        code_row = next((row for row in knowledge.get("room_code_examples", []) if row["code"].upper() == code.upper()), None)
        if code_row:
            parent_name = code_row.get("type", "")
            parent = next((row for row in knowledge["locations"] if row["name"] == parent_name or parent_name in row.get("aliases", [])), None)
            if parent:
                route_location_ids.add(parent["id"])
        # Generated room-code candidates carry the parent directly in the resolver result.
        for candidate in location.get("candidates", []):
            if candidate.get("location_id") == location_id and candidate.get("parent"):
                route_location_ids.add(candidate["parent"])

    # Explicit building and scope recognition handles location descriptions not represented
    # as a single canonical location record (e.g. campus-wide infrastructure).
    aliases = {
        "HOSTEL-A": ("a block hostel", "a block", "a hostel", "girls hostel"),
        "HOSTEL-B": ("b block hostel", "b block", "b hostel", "boys hostel b"),
        "HOSTEL-C": ("c block hostel", "c block", "c hostel", "boys hostel c"),
        "ACADEMIC-BLOCK": ("academic block", "acad block", "computer lab", "lecture hall", "classroom"),
        "ADMIN-BLOCK": ("admin block", "admin building"),
        "TNP-BLOCK": ("tnp block", "training and placement", "placement cell"),
        "OPEN-AIR-THEATRE": ("open air theatre", "plaza"),
        "DINING-MESS": ("mess", "canteen", "dining building", "dining hall"),
        "GATE-01": ("gate 01", "gate 1", "main gate"),
        "GATE-02": ("gate 2", "back gate"),
        "SPORTS-GROUNDS": ("sports ground", "sports grounds", "sports field"),
    }
    for loc_id, phrases in aliases.items():
        if any(_contains(text, phrase) for phrase in phrases):
            route_location_ids.add(loc_id)
    campus_wide = any(_contains(text, phrase) for phrase in (
        "campus wide infrastructure", "campus-wide infrastructure", "campus wide", "across campus", "whole campus"
    ))
    all_hostels = any(_contains(text, phrase) for phrase in ("all hostels", "every hostel", "across all hostels"))
    if all_hostels:
        route_location_ids.add("ALL-HOSTELS")
    if campus_wide:
        route_location_ids.add("CAMPUS-WIDE-INFRASTRUCTURE")

    # Emergency override: every configured council member receives the proposal.
    emergency = priority in {"critical", "emergency"} or bool(triage.get("escalation"))
    eligible_roles = []
    matched_rules = []
    if emergency:
        eligible_roles = list(routing.get("eligible_roles", ROLES))
        matched_rules = [{"id": "EMERGENCY-ALL-COUNCIL"}]
    else:
        for rule in rules:
            ids = rule.get("location_ids", [])
            types = rule.get("issue_types", [])
            location_match = bool(route_location_ids.intersection(ids))
            issue_match = "*" in types or issue in [_normalize(item) for item in types]
            if location_match and issue_match:
                matched_rules.append(rule)
                for role in (rule.get("roles") or ([rule.get("role")] if rule.get("role") else [])):
                    if role and role not in eligible_roles:
                        eligible_roles.append(role)

    # Do not ask for confirmations beyond a genuine missing/ambiguous location.
    if not location.get("verified") and not route_location_ids:
        result.update(assignment_status="PENDING_CONFIRMATION",
                      assignment_rationale="Location is unclear; a location-dependent routing decision cannot yet be made.",
                      next_action=location.get("question") or "Which building or area is affected?")
        return result
    if not matched_rules or not eligible_roles:
        result["approval_required"] = True
        result["assignment_rationale"] = "No approved routing rule matches the stated location and issue type."
        result["next_action"] = "Location is known, but the owner-approved routing policy has no recipient for this area; human review is required."
        return result

    result.update(assignment_target_role=eligible_roles[0], assignment_target_roles=eligible_roles,
                  assignment_status="PROPOSED",
                  assignment_rationale=("Emergency override: all council members included."
                      if emergency else "All matching council roles are included under the approved routing policy. Matched rules: " +
                      ", ".join(rule["id"] for rule in matched_rules)),
                  approval_required=bool(triage.get("approval_required", False)) or emergency,
                  next_action=("Emergency escalation proposed to all council members for immediate human review."
                      if emergency else "Council routing is proposed for human review; no notification or dispatch has occurred."))
    return result


def _verify(assignment, role):
    valid = role in ROLES and role == assignment.get("assignment_target_role") and assignment.get("assignment_status") == "PROPOSED"
    return {"valid": valid, "reason": "Role matches the supported proposal." if valid else "No supported matching council proposal.",
            "approval_required": assignment.get("approval_required", True)}


HEADINGS = ("Complaint", "Location", "Issue and priority", "Possible duplicate", "Council routing", "Next step")


def format_report(result):
    """Concise, user-facing result; detailed diagnostic data remains in structured fields."""
    loc, tri, dup, assign = (result[k] for k in ("location", "triage", "duplicates", "assignment"))
    if result.get("intent") == "information":
        return result.get("answer", "I couldn't find that location in the campus knowledge base.")
    parts = [f"**Complaint:** {result['complaint'].strip()}"]
    if loc.get("canonical_location"):
        parts.append(f"**Location:** {loc['canonical_location']}")
    else:
        parts.append("**Location:** Not identified yet.")
    parts.append(f"**Issue:** {tri['issue_type'].capitalize()} · **Priority:** {tri['priority'].upper()}")
    if dup.get("decision") == "POSSIBLE_DUPLICATE":
        parts.append("**Possible duplicate:** A similar report exists in the local demo records; please review before treating this as new.")
    else:
        parts.append("**Possible duplicate:** No likely match in the local demo records.")
    roles = assign.get("assignment_target_roles") or ([assign.get("assignment_target_role")] if assign.get("assignment_target_role") else [])
    if assign.get("assignment_status") == "PROPOSED" and roles:
        parts.append("**Council routing proposal:** " + ", ".join(roles) + ".")
    elif assign.get("assignment_status") == "PENDING_CONFIRMATION":
        parts.append("**Council routing:** " + (assign.get("next_action") or "Please confirm the location or affected scope."))
    else:
        parts.append("**Council routing:** Pending review because no matching approved rule is available.")
    questions = list(dict.fromkeys([q for q in result.get("questions", []) if q]))
    if questions:
        parts.append("**Please clarify:** " + questions[0])
    elif tri.get("priority") in {"high", "critical"}:
        parts.append("**Safety:** Human review is required before action.")
    else:
        parts.append("**Status:** Routing is a proposal only; it has not been saved or sent.")
    return "\n\n".join(parts)


def assess(complaint, location_text, confirmation=None, source_conflict="", routing=None, records=None):
    if not complaint.strip():
        raise ValueError("Complaint text is required")
    loc = resolve_location(location_text or complaint, confirmation, source_conflict)
    # Explicit all-hostel scope is a clear location for routing, not an unknown building.
    stated_location = _normalize(location_text or complaint)
    if any(_contains(stated_location, phrase) for phrase in ("all hostels", "every hostel", "across all hostels")):
        loc.update(location_status="KNOWN_LOCATION", canonical_location="All Hostels", location_id="ALL-HOSTELS",
                   verified=True, question=None, scope_status="AS_REPORTED")
    # Informational questions must not enter complaint triage, duplicate checking, or assignment.
    norm_complaint = _normalize(complaint)
    asks_location = bool(re.match(r"^(where is|where s|where are|what is|what s|tell me about|locate)\b", norm_complaint))
    if asks_location:
        answer = loc.get("direct_answer")
        if not answer:
            answer = _location_answer(complaint, loc.get("candidates", []))
        if not answer:
            answer = "I couldn't identify that location in the campus knowledge. Please provide a known building name or room code."
        result = {"complaint": complaint, "location": loc, "intent": "information", "answer": answer,
                  "workflow_status": "INFORMATION_RESPONSE", "persisted": False}
        result["report"] = answer
        return result
    # Scope is a property of the full complaint, even when location extraction is empty.
    if any(_contains(norm_complaint, p) for p in ("everywhere", "somewhere on campus", "in multiple places")):
        # Ask only if the scope/location is genuinely too vague to route.
        if not loc.get("verified") and not loc.get("location_id"):
            loc["scope_status"] = "NEEDS_CLARIFICATION"
            loc["question"] = "Which building or area is affected?"
    tri = _classify(complaint)
    dup = _duplicate(complaint, location_text, records)
    assign = _assign(tri["issue_type"], loc, tri, routing)
    questions = list(dict.fromkeys([q for q in [loc.get("question")] if q]))
    next_action = tri["escalation"] or (questions[0] if questions else assign["next_action"])
    result = {"complaint": complaint, "location": loc, "triage": tri, "duplicates": dup,
              "assignment": assign, "questions": questions, "next_action": next_action,
              "intent": "complaint", "workflow_status": "ASSESSMENT_ONLY", "persisted": False}
    result["report"] = format_report(result)
    return result
