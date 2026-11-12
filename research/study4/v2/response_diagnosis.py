"""Offline-only typed response inspection. Does not read credentials or call a provider."""
from pathlib import Path

from .contracts import strict_json
from .executor import FIELDS

ROOT = Path(__file__).parent
TOP_KEYS = {"id", "model", "status", "error", "incomplete_details", "output", "usage", "service_tier"}
OUTPUT_TYPES = {"message", "reasoning", "function_call", "web_search_call", "file_search_call",
                "code_interpreter_call", "compaction"}
APP_KEYS = {"tool", "arguments", "action", "person_id", "intent", "include_value_ids", "question"}
ARG_KEYS = set().union(*FIELDS.values())


class ResponseStageError(ValueError):
    def __init__(self, stage, cause_type, frames):
        super().__init__("Response validation failed at " + stage)
        self.stage, self.cause_type, self.validator_frames = stage, cause_type, frames


def validation_frames(error):
    frames = []
    trace = error.__traceback__
    while trace is not None:
        path = Path(trace.tb_frame.f_code.co_filename).resolve()
        if path.is_relative_to(ROOT.resolve()):
            frames.append({"file": path.relative_to(ROOT.resolve()).as_posix(),
                           "function": trace.tb_frame.f_code.co_name, "line": trace.tb_lineno})
        trace = trace.tb_next
    return frames


def at_stage(stage, validate):
    try:
        return validate()
    except ResponseStageError:
        raise
    except (ValueError, KeyError, TypeError, IndexError, UnicodeError) as error:
        raise ResponseStageError(stage, type(error).__name__, validation_frames(error)) from None


def known_enum(value, allowed):
    return value if isinstance(value, str) and value in allowed else "unrecognized"


def key_shape(value, allowed):
    if not isinstance(value, dict):
        return {"type": type(value).__name__}
    return {"type": "dict", "known_keys": sorted(set(value) & allowed),
            "other_key_count": len(set(value) - allowed),
            "known_value_types": {key: type(value[key]).__name__ for key in sorted(set(value) & allowed)}}


def inspect_response_shape(raw):
    try:
        response = strict_json(raw)
    except (ValueError, UnicodeError) as error:
        return {"parse_error_type": type(error).__name__}
    result = {"root": key_shape(response, TOP_KEYS)}
    if not isinstance(response, dict):
        return result
    result["output_type"] = type(response.get("output")).__name__
    output = response.get("output")
    if not isinstance(output, list):
        return result
    result["output_count"] = len(output)
    items = []
    for item in output[:16]:
        row = {"shape": key_shape(item, {"type", "role", "content", "summary", "id", "status",
                                       "name", "arguments", "call_id"})}
        if isinstance(item, dict):
            row["type"] = known_enum(item.get("type"), OUTPUT_TYPES)
            row["role"] = known_enum(item.get("role"), ("assistant", "user", "system"))
            if item.get("type") == "function_call":
                row["function"] = known_enum(item.get("name"), set(FIELDS) | {"choose_help", "compose_help_request"})
                if isinstance(item.get("arguments"), str):
                    try:
                        row["argument_shape"] = key_shape(strict_json(item["arguments"]),
                                                         ARG_KEYS | APP_KEYS)
                    except ValueError as error:
                        row["arguments_parse_error_type"] = type(error).__name__
            content = item.get("content")
            row["content_type"] = type(content).__name__
            if isinstance(content, list):
                row["content_count"] = len(content)
                parts = []
                for part in content[:16]:
                    details = {"shape": key_shape(part, {"type", "text", "refusal", "annotations", "logprobs"})}
                    if isinstance(part, dict):
                        details["type"] = known_enum(part.get("type"), ("output_text", "refusal", "input_text"))
                        if isinstance(part.get("text"), str):
                            try:
                                app = strict_json(part["text"])
                                details["application_shape"] = key_shape(app, APP_KEYS)
                                if isinstance(app, dict):
                                    details["tool"] = known_enum(app.get("tool"), FIELDS)
                                    if isinstance(app.get("arguments"), str):
                                        try:
                                            details["argument_shape"] = key_shape(strict_json(app["arguments"]), ARG_KEYS)
                                        except ValueError as error:
                                            details["arguments_parse_error_type"] = type(error).__name__
                            except ValueError as error:
                                details["application_parse_error_type"] = type(error).__name__
                    parts.append(details)
                row["content"] = parts
        items.append(row)
    result["output"] = items
    result["no_arbitrary_response_text_or_key_values_retained"] = True
    return result


def diagnose_offline(raw, operation, request, plan, *, provenance):
    """Same unchanged validators; syntheses MUST be marked, never actual-body recovery."""
    from .admission import decode_response, prepare_request
    result = {"provenance": provenance, "shape": inspect_response_shape(raw)}
    try:
        _, bound, observation, assistance = prepare_request(request, operation, plan)
        decode_response(raw, operation, observation, assistance, plan, bound)
        result["accepted"] = True
    except (ValueError, KeyError, TypeError, IndexError, UnicodeError) as error:
        result.update(accepted=False, exception_type=type(error).__name__)
        result["validator_frames"] = getattr(error, "validator_frames", validation_frames(error))
        if isinstance(error, ResponseStageError):
            result.update(stage=error.stage, cause_type=error.cause_type)
    return result
