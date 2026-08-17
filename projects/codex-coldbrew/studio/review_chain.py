# -*- coding: utf-8 -*-
"""Local request/review chain with restart-safe, redacted state.

The adapter does not perform network I/O. Callers own transport and pass the
in-memory placeholder contract to their review client. Only a compact request
summary and review lifecycle events are written to disk.
"""

from __future__ import annotations

import copy
import json
import os
import re
import tempfile
import uuid
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


REVIEW_ENDPOINT = "REVIEW_ENDPOINT"
REQUEST_BODY = "REQUEST_BODY"
REVIEW_FLAG = "REVIEW_FLAG"

PLACEHOLDER_CONTRACT = {
    "endpoint": REVIEW_ENDPOINT,
    "body": REQUEST_BODY,
    "flag": REVIEW_FLAG,
}

STATE_SCHEMA = 1
TERMINAL_STATUSES = frozenset({"allowed", "rejected", "bypassed"})
RECOVERABLE_STATUSES = frozenset({"awaiting_review", "interrupted", "retry_pending"})
RETRYABLE_STATUSES = frozenset({"interrupted", "retry_pending"})
VALID_STATUSES = frozenset({"idle", *TERMINAL_STATUSES, *RECOVERABLE_STATUSES})
RESPONSE_POLICY = {
    "ALLOW": "allowed",
    "APPROVE": "allowed",
    "APPROVED": "allowed",
    "PASS": "allowed",
    "DENY": "rejected",
    "REJECT": "rejected",
    "REJECTED": "rejected",
    "RETRY": "retry_pending",
    "RETRYABLE": "retry_pending",
    "INTERRUPT": "interrupted",
    "INTERRUPTED": "interrupted",
    "ABORT": "interrupted",
}

_SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_SAFE_CODE = re.compile(r"^[A-Za-z0-9._:-]{1,96}$")
_METHOD = re.compile(r"^[A-Z][A-Z0-9_-]{0,31}$")
_SENSITIVE_PATH_LABELS = frozenset(
    {"access_token", "apikey", "api-key", "api_key", "auth", "credential", "key", "password", "secret", "token"}
)
_ALLOWED_DETAIL_KEYS = frozenset(
    {
        "body_bytes",
        "body_type",
        "endpoint",
        "header_names",
        "matched_rule_ids",
        "method",
        "previous_status",
    }
)


class ReviewChainError(RuntimeError):
    """Expected request-chain or state-contract failure."""


class RuleConfigError(ReviewChainError):
    """A declarative review rule is malformed."""


class StateConflictError(ReviewChainError):
    """An operation conflicts with the persisted session lifecycle."""


def _require_safe_id(value: str, label: str) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise ReviewChainError(f"{label} must match {_SAFE_ID.pattern}")
    return value


def _require_safe_code(value: str, label: str) -> str:
    if not isinstance(value, str) or _SAFE_CODE.fullmatch(value) is None:
        raise ReviewChainError(f"{label} must match {_SAFE_CODE.pattern}")
    return value


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(clock: Callable[[], datetime]) -> str:
    value = clock()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ReviewChainError("REQUEST_BODY must be JSON-compatible") from exc


def _body_type(value: Any) -> str:
    if isinstance(value, Mapping):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    return "unknown"


def _redact_path(path: str) -> str:
    parts = path.split("/")
    output: list[str] = []
    redact_next = False
    for part in parts:
        if redact_next:
            output.append("<redacted>")
            redact_next = False
            continue
        normalized = part.casefold()
        if normalized in _SENSITIVE_PATH_LABELS:
            output.append(part)
            redact_next = True
        elif len(part) > 96:
            output.append("<long-segment>")
        else:
            output.append(part)
    return "/".join(output)


def safe_endpoint(endpoint: str) -> str:
    """Remove credentials, query data, fragments, and obvious secret segments."""
    value = endpoint.strip()
    parsed = urlsplit(value)
    path = _redact_path(parsed.path or ("/" if parsed.netloc else value.split("?", 1)[0].split("#", 1)[0]))
    if not parsed.scheme or not parsed.netloc:
        return path[:1024]

    host = parsed.hostname or ""
    try:
        port = f":{parsed.port}" if parsed.port is not None else ""
    except ValueError:
        port = ""
    return f"{parsed.scheme.casefold()}://{host.casefold()}{port}{path}"[:1024]


def _body_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return _json_bytes(value).decode("utf-8")


def _string_tuple(value: Any, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise RuleConfigError(f"{label} must be a list of strings")
    result = tuple(value)
    if any(not isinstance(item, str) or not item for item in result):
        raise RuleConfigError(f"{label} must contain non-empty strings")
    return result


@dataclass(frozen=True, slots=True)
class OutboundRequest:
    """A full request held in memory while only ``safe_summary`` is persisted."""

    request_id: str
    session_id: str
    method: str
    endpoint: str
    body: Any
    headers: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_safe_id(self.request_id, "request_id")
        _require_safe_id(self.session_id, "session_id")
        method = self.method.strip().upper()
        if _METHOD.fullmatch(method) is None:
            raise ReviewChainError("method is invalid")
        if not isinstance(self.endpoint, str) or not self.endpoint.strip():
            raise ReviewChainError("endpoint must be a non-empty string")
        if len(self.endpoint) > 8192:
            raise ReviewChainError("endpoint is too long")
        if not isinstance(self.headers, Mapping) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in self.headers.items()
        ):
            raise ReviewChainError("headers must map strings to strings")
        _json_bytes(self.body)
        object.__setattr__(self, "method", method)
        object.__setattr__(self, "headers", dict(self.headers))

    def safe_summary(self) -> dict[str, Any]:
        body = _json_bytes(self.body)
        return {
            "method": self.method,
            "endpoint": safe_endpoint(self.endpoint),
            "body_type": _body_type(self.body),
            "body_bytes": len(body),
            "header_names": sorted(str(key).casefold() for key in self.headers),
        }


@dataclass(frozen=True, slots=True)
class ReviewRule:
    """Declarative matching rule; all conditions are optional and cumulative."""

    rule_id: str
    endpoint_pattern: str = ".*"
    methods: tuple[str, ...] = ()
    body_keys_all: tuple[str, ...] = ()
    body_keys_any: tuple[str, ...] = ()
    body_pattern: str | None = None
    header_names_all: tuple[str, ...] = ()
    review_flag: str = REVIEW_FLAG
    priority: int = 0
    enabled: bool = True
    _endpoint_regex: re.Pattern[str] = field(init=False, repr=False, compare=False)
    _body_regex: re.Pattern[str] | None = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        try:
            _require_safe_id(self.rule_id, "rule_id")
            _require_safe_code(self.review_flag, "review_flag")
        except ReviewChainError as exc:
            raise RuleConfigError(str(exc)) from exc
        if not isinstance(self.priority, int) or isinstance(self.priority, bool):
            raise RuleConfigError("priority must be an integer")
        if not isinstance(self.enabled, bool):
            raise RuleConfigError("enabled must be a boolean")
        methods = tuple(method.strip().upper() for method in self.methods)
        if any(_METHOD.fullmatch(method) is None for method in methods):
            raise RuleConfigError("methods contains an invalid method")
        body_keys_all = _string_tuple(self.body_keys_all, "body_keys_all")
        body_keys_any = _string_tuple(self.body_keys_any, "body_keys_any")
        header_names_all = tuple(
            item.casefold() for item in _string_tuple(self.header_names_all, "header_names_all")
        )
        try:
            endpoint_regex = re.compile(self.endpoint_pattern)
            body_regex = re.compile(self.body_pattern) if self.body_pattern is not None else None
        except (re.error, TypeError) as exc:
            raise RuleConfigError(f"invalid rule regex: {exc}") from exc
        object.__setattr__(self, "methods", methods)
        object.__setattr__(self, "body_keys_all", body_keys_all)
        object.__setattr__(self, "body_keys_any", body_keys_any)
        object.__setattr__(self, "header_names_all", header_names_all)
        object.__setattr__(self, "_endpoint_regex", endpoint_regex)
        object.__setattr__(self, "_body_regex", body_regex)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ReviewRule":
        allowed = {
            "body_keys_all",
            "body_keys_any",
            "body_pattern",
            "enabled",
            "endpoint_pattern",
            "header_names_all",
            "methods",
            "priority",
            "review_flag",
            "rule_id",
        }
        unknown = set(value) - allowed
        if unknown:
            raise RuleConfigError(f"unknown rule fields: {sorted(unknown)}")
        if "rule_id" not in value:
            raise RuleConfigError("rule_id is required")
        return cls(
            rule_id=value["rule_id"],
            endpoint_pattern=value.get("endpoint_pattern", ".*"),
            methods=_string_tuple(value.get("methods"), "methods"),
            body_keys_all=_string_tuple(value.get("body_keys_all"), "body_keys_all"),
            body_keys_any=_string_tuple(value.get("body_keys_any"), "body_keys_any"),
            body_pattern=value.get("body_pattern"),
            header_names_all=_string_tuple(value.get("header_names_all"), "header_names_all"),
            review_flag=value.get("review_flag", REVIEW_FLAG),
            priority=value.get("priority", 0),
            enabled=value.get("enabled", True),
        )

    def matches(self, request: OutboundRequest) -> bool:
        if not self.enabled:
            return False
        if self.methods and request.method not in self.methods:
            return False
        if self._endpoint_regex.search(safe_endpoint(request.endpoint)) is None:
            return False
        body_keys = set(request.body) if isinstance(request.body, Mapping) else set()
        if self.body_keys_all and not set(self.body_keys_all).issubset(body_keys):
            return False
        if self.body_keys_any and not set(self.body_keys_any).intersection(body_keys):
            return False
        header_names = {str(name).casefold() for name in request.headers}
        if self.header_names_all and not set(self.header_names_all).issubset(header_names):
            return False
        return self._body_regex is None or self._body_regex.search(_body_text(request.body)) is not None


def _validate_details(details: Mapping[str, Any]) -> dict[str, Any]:
    unknown = set(details) - _ALLOWED_DETAIL_KEYS
    if unknown:
        raise ReviewChainError(f"unsafe event detail fields: {sorted(unknown)}")
    try:
        encoded = _json_bytes(dict(details))
    except ReviewChainError as exc:
        raise ReviewChainError("event details are not JSON-compatible") from exc
    if len(encoded) > 8192:
        raise ReviewChainError("event details are too large")
    return copy.deepcopy(dict(details))


@dataclass(frozen=True, slots=True)
class ReviewEvent:
    event_id: str
    sequence: int
    kind: str
    timestamp: str
    session_id: str
    request_id: str | None
    attempt: int
    rule_ids: tuple[str, ...] = ()
    review_flag: str | None = None
    code: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_safe_id(self.event_id, "event_id")
        _require_safe_id(self.session_id, "session_id")
        if self.request_id is not None:
            _require_safe_id(self.request_id, "request_id")
        _require_safe_code(self.kind, "event kind")
        if self.review_flag is not None:
            _require_safe_code(self.review_flag, "review_flag")
        if self.code is not None:
            _require_safe_code(self.code, "event code")
        if not isinstance(self.sequence, int) or self.sequence < 1:
            raise ReviewChainError("event sequence must be positive")
        if not isinstance(self.attempt, int) or self.attempt < 0:
            raise ReviewChainError("event attempt must be non-negative")
        if not isinstance(self.timestamp, str) or len(self.timestamp) > 64:
            raise ReviewChainError("event timestamp is invalid")
        rule_ids = tuple(_require_safe_id(item, "rule_id") for item in self.rule_ids)
        object.__setattr__(self, "rule_ids", rule_ids)
        object.__setattr__(self, "details", _validate_details(self.details))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "sequence": self.sequence,
            "kind": self.kind,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "attempt": self.attempt,
            "rule_ids": list(self.rule_ids),
            "review_flag": self.review_flag,
            "code": self.code,
            "details": copy.deepcopy(dict(self.details)),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ReviewEvent":
        expected = {
            "attempt",
            "code",
            "details",
            "event_id",
            "kind",
            "request_id",
            "review_flag",
            "rule_ids",
            "sequence",
            "session_id",
            "timestamp",
        }
        if set(value) != expected:
            raise ReviewChainError("persisted event fields are invalid")
        return cls(
            event_id=value["event_id"],
            sequence=value["sequence"],
            kind=value["kind"],
            timestamp=value["timestamp"],
            session_id=value["session_id"],
            request_id=value["request_id"],
            attempt=value["attempt"],
            rule_ids=tuple(value["rule_ids"]),
            review_flag=value["review_flag"],
            code=value["code"],
            details=value["details"],
        )


@dataclass(slots=True)
class SessionState:
    session_id: str
    created_at: str
    updated_at: str
    status: str = "idle"
    active_request_id: str | None = None
    attempt: int = 0
    matched_rule_ids: list[str] = field(default_factory=list)
    request_summary: dict[str, Any] | None = None
    review_flag: str | None = None
    restart_count: int = 0
    next_sequence: int = 1
    events: list[ReviewEvent] = field(default_factory=list)
    schema: int = STATE_SCHEMA

    def __post_init__(self) -> None:
        _require_safe_id(self.session_id, "session_id")
        if self.schema != STATE_SCHEMA:
            raise ReviewChainError(f"unsupported state schema: {self.schema}")
        if self.status not in VALID_STATUSES:
            raise ReviewChainError(f"invalid session status: {self.status}")
        if self.active_request_id is not None:
            _require_safe_id(self.active_request_id, "active_request_id")
        if self.review_flag is not None:
            _require_safe_code(self.review_flag, "review_flag")
        if not isinstance(self.attempt, int) or self.attempt < 0:
            raise ReviewChainError("attempt must be non-negative")
        if not isinstance(self.restart_count, int) or self.restart_count < 0:
            raise ReviewChainError("restart_count must be non-negative")
        if not isinstance(self.next_sequence, int) or self.next_sequence < 1:
            raise ReviewChainError("next_sequence must be positive")
        self.matched_rule_ids = [
            _require_safe_id(item, "matched_rule_id") for item in self.matched_rule_ids
        ]
        if self.request_summary is not None:
            self.request_summary = _validate_details(self.request_summary)
        if any(event.session_id != self.session_id for event in self.events):
            raise ReviewChainError("event session_id mismatch")
        sequences = [event.sequence for event in self.events]
        if sequences != sorted(set(sequences)):
            raise ReviewChainError("event sequences must be unique and ordered")
        if sequences and self.next_sequence <= sequences[-1]:
            raise ReviewChainError("next_sequence does not follow persisted events")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "active_request_id": self.active_request_id,
            "attempt": self.attempt,
            "matched_rule_ids": list(self.matched_rule_ids),
            "request_summary": copy.deepcopy(self.request_summary),
            "review_flag": self.review_flag,
            "restart_count": self.restart_count,
            "next_sequence": self.next_sequence,
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SessionState":
        expected = {
            "active_request_id",
            "attempt",
            "created_at",
            "events",
            "matched_rule_ids",
            "next_sequence",
            "request_summary",
            "restart_count",
            "review_flag",
            "schema",
            "session_id",
            "status",
            "updated_at",
        }
        if set(value) != expected:
            raise ReviewChainError("persisted session fields are invalid")
        if not isinstance(value["events"], list):
            raise ReviewChainError("events must be a list")
        return cls(
            schema=value["schema"],
            session_id=value["session_id"],
            created_at=value["created_at"],
            updated_at=value["updated_at"],
            status=value["status"],
            active_request_id=value["active_request_id"],
            attempt=value["attempt"],
            matched_rule_ids=list(value["matched_rule_ids"]),
            request_summary=value["request_summary"],
            review_flag=value["review_flag"],
            restart_count=value["restart_count"],
            next_sequence=value["next_sequence"],
            events=[ReviewEvent.from_dict(item) for item in value["events"]],
        )


@dataclass(frozen=True, slots=True)
class ReviewDecision:
    request_id: str
    intercepted: bool
    status: str
    matched_rule_ids: tuple[str, ...]
    contract: Mapping[str, Any] | None


class ReviewChainAdapter:
    """Persisted local lifecycle adapter for application-level review calls."""

    def __init__(
        self,
        state_path: Path,
        rules: Iterable[ReviewRule | Mapping[str, Any]],
        *,
        review_endpoint: str = REVIEW_ENDPOINT,
        response_policy: Mapping[str, str] | None = None,
        clock: Callable[[], datetime] = _utc_now,
        event_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.state_path = Path(state_path)
        if not isinstance(review_endpoint, str) or not review_endpoint:
            raise ReviewChainError("review_endpoint must be a non-empty string")
        self.review_endpoint = review_endpoint
        normalized: list[ReviewRule] = []
        for rule in rules:
            normalized.append(rule if isinstance(rule, ReviewRule) else ReviewRule.from_mapping(rule))
        self.rules = tuple(sorted(normalized, key=lambda item: item.priority, reverse=True))
        policy = dict(RESPONSE_POLICY if response_policy is None else response_policy)
        if not policy:
            raise ReviewChainError("response_policy must not be empty")
        self.response_policy: dict[str, str] = {}
        for flag_value, status in policy.items():
            normalized_flag = _require_safe_code(str(flag_value).upper(), "response flag")
            if status not in {"allowed", "rejected", "retry_pending", "interrupted"}:
                raise ReviewChainError(f"invalid response status: {status}")
            self.response_policy[normalized_flag] = status
        self._clock = clock
        self._event_id_factory = event_id_factory or (lambda: uuid.uuid4().hex)
        self._state = self._read_state()

    @property
    def state(self) -> SessionState | None:
        return SessionState.from_dict(self._state.to_dict()) if self._state is not None else None

    def _read_state(self) -> SessionState | None:
        if not self.state_path.exists():
            return None
        if self.state_path.is_symlink():
            raise ReviewChainError(f"refusing to read state symlink: {self.state_path}")
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ReviewChainError(f"unable to read review state: {exc}") from exc
        if not isinstance(value, dict):
            raise ReviewChainError("persisted review state must be an object")
        return SessionState.from_dict(value)

    def _write_state(self) -> None:
        if self._state is None:
            raise ReviewChainError("session state is not initialized")
        if self.state_path.is_symlink():
            raise ReviewChainError(f"refusing to overwrite state symlink: {self.state_path}")
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = (json.dumps(self._state.to_dict(), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        descriptor, name = tempfile.mkstemp(prefix=f".{self.state_path.name}.", dir=self.state_path.parent)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, self.state_path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _require_state(self, session_id: str | None = None) -> SessionState:
        if self._state is None:
            raise StateConflictError("session state does not exist")
        if session_id is not None and self._state.session_id != session_id:
            raise StateConflictError("session_id does not match persisted state")
        return self._state

    def _new_state(self, session_id: str) -> SessionState:
        created_at = _timestamp(self._clock)
        return SessionState(session_id=session_id, created_at=created_at, updated_at=created_at)

    def _append_event(
        self,
        kind: str,
        *,
        request_id: str | None,
        rule_ids: Iterable[str] = (),
        review_flag: str | None = None,
        code: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> ReviewEvent:
        state = self._require_state()
        event = ReviewEvent(
            event_id=_require_safe_id(self._event_id_factory(), "event_id"),
            sequence=state.next_sequence,
            kind=kind,
            timestamp=_timestamp(self._clock),
            session_id=state.session_id,
            request_id=request_id,
            attempt=state.attempt,
            rule_ids=tuple(rule_ids),
            review_flag=review_flag,
            code=code,
            details=details or {},
        )
        state.events.append(event)
        state.next_sequence += 1
        state.updated_at = event.timestamp
        return event

    def _decision_contract(self, request: OutboundRequest, flag_value: str) -> dict[str, Any]:
        return {
            REVIEW_ENDPOINT: self.review_endpoint,
            REQUEST_BODY: copy.deepcopy(request.body),
            REVIEW_FLAG: flag_value,
        }

    def _evaluate(self, request: OutboundRequest) -> ReviewDecision:
        state = self._require_state(request.session_id)
        summary = request.safe_summary()
        state.request_summary = summary
        self._append_event("request", request_id=request.request_id, details=summary)
        matches = tuple(rule for rule in self.rules if rule.matches(request))
        if not matches:
            state.status = "bypassed"
            state.active_request_id = None
            state.matched_rule_ids = []
            state.review_flag = None
            self._append_event("bypass", request_id=request.request_id, code="no-rule-match")
            self._write_state()
            return ReviewDecision(request.request_id, False, state.status, (), None)

        rule_ids = tuple(rule.rule_id for rule in matches)
        flag_value = matches[0].review_flag
        state.status = "awaiting_review"
        state.active_request_id = request.request_id
        state.matched_rule_ids = list(rule_ids)
        state.review_flag = flag_value
        self._append_event(
            "hit",
            request_id=request.request_id,
            rule_ids=rule_ids,
            review_flag=flag_value,
            details={"matched_rule_ids": list(rule_ids)},
        )
        self._append_event(
            "review_request",
            request_id=request.request_id,
            rule_ids=rule_ids,
            review_flag=flag_value,
        )
        self._write_state()
        return ReviewDecision(
            request_id=request.request_id,
            intercepted=True,
            status=state.status,
            matched_rule_ids=rule_ids,
            contract=self._decision_contract(request, flag_value),
        )

    def intercept(self, request: OutboundRequest) -> ReviewDecision:
        if self._state is None:
            self._state = self._new_state(request.session_id)
        state = self._require_state(request.session_id)
        if state.status in RECOVERABLE_STATUSES:
            raise StateConflictError("an unfinished request must be resolved, recovered, or retried first")
        state.active_request_id = request.request_id
        state.attempt = 1
        state.matched_rule_ids = []
        state.review_flag = None
        return self._evaluate(request)

    def record_response(self, request_id: str, review_flag: str) -> SessionState:
        state = self._require_state()
        _require_safe_id(request_id, "request_id")
        flag_value = _require_safe_code(review_flag.upper(), "review_flag")
        if state.status != "awaiting_review" or state.active_request_id != request_id:
            raise StateConflictError("no matching review request is awaiting a response")
        if flag_value not in self.response_policy:
            raise ReviewChainError(f"unmapped response flag: {flag_value}")
        status = self.response_policy[flag_value]
        self._append_event(
            "response",
            request_id=request_id,
            rule_ids=state.matched_rule_ids,
            review_flag=flag_value,
        )
        state.status = status
        state.review_flag = flag_value
        if status in TERMINAL_STATUSES:
            state.active_request_id = None
        elif status == "interrupted":
            self._append_event(
                "interrupted",
                request_id=request_id,
                rule_ids=state.matched_rule_ids,
                review_flag=flag_value,
                code="response-flag",
            )
        self._write_state()
        return self.state  # type: ignore[return-value]

    def interrupt(self, request_id: str, reason_code: str = "caller-interrupted") -> SessionState:
        state = self._require_state()
        _require_safe_id(request_id, "request_id")
        _require_safe_code(reason_code, "reason_code")
        if state.status != "awaiting_review" or state.active_request_id != request_id:
            raise StateConflictError("no matching review request can be interrupted")
        state.status = "interrupted"
        self._append_event(
            "interrupted",
            request_id=request_id,
            rule_ids=state.matched_rule_ids,
            code=reason_code,
        )
        self._write_state()
        return self.state  # type: ignore[return-value]

    def retry(self, request: OutboundRequest) -> ReviewDecision:
        state = self._require_state(request.session_id)
        if state.status not in RETRYABLE_STATUSES or state.active_request_id != request.request_id:
            raise StateConflictError("request is not waiting for retry")
        state.attempt += 1
        self._append_event(
            "retry",
            request_id=request.request_id,
            rule_ids=state.matched_rule_ids,
            code="caller-resubmitted",
        )
        return self._evaluate(request)

    def recover(self, session_id: str) -> SessionState:
        state = self._require_state(session_id)
        if state.status not in RECOVERABLE_STATUSES:
            return self.state  # type: ignore[return-value]
        previous = state.status
        state.status = "retry_pending"
        state.restart_count += 1
        self._append_event(
            "recovered",
            request_id=state.active_request_id,
            rule_ids=state.matched_rule_ids,
            code="restart-requires-resubmit",
            details={"previous_status": previous},
        )
        self._write_state()
        return self.state  # type: ignore[return-value]


ReviewChain = ReviewChainAdapter


def run_self_test(state_root: Path) -> dict[str, Any]:
    """Exercise the complete local chain with a deterministic synthetic request."""

    root = Path(state_root)
    state_path = root if root.suffix == ".json" else root / "self-test-state.json"
    if state_path.is_symlink():
        raise ReviewChainError(f"refusing to replace state symlink: {state_path}")
    if state_path.exists():
        state_path.unlink()
    rules = [
        {
            "rule_id": "coldbrew-local-review",
            "endpoint_pattern": r"/REVIEW_ENDPOINT$",
            "methods": ["POST"],
            "body_keys_all": ["request", "session"],
            "body_pattern": "REQUEST_BODY",
            "header_names_all": ["authorization"],
            "review_flag": REVIEW_FLAG,
            "priority": 100,
        }
    ]
    request = OutboundRequest(
        request_id="coldbrew-self-test-request",
        session_id="coldbrew-self-test-session",
        method="POST",
        endpoint="https://HOST/REVIEW_ENDPOINT?token=TOKEN",
        headers={"Authorization": "Bearer TOKEN", "Content-Type": "application/json"},
        body={"request": REQUEST_BODY, "session": "SERIAL"},
    )
    adapter = ReviewChainAdapter(state_path, rules)
    first = adapter.intercept(request)
    adapter.interrupt(request.request_id, "fixture-interrupt")
    second = adapter.retry(request)
    adapter.record_response(request.request_id, "RETRY")

    restarted = ReviewChainAdapter(state_path, rules)
    restarted.recover(request.session_id)
    third = restarted.retry(request)
    final = restarted.record_response(request.request_id, "ALLOW")
    kinds = [event.kind for event in final.events]
    expected = {"request", "hit", "review_request", "interrupted", "retry", "response", "recovered"}
    persisted = state_path.read_text(encoding="utf-8")
    redacted = "Bearer TOKEN" not in persisted and "?token=TOKEN" not in persisted
    ok = (
        first.intercepted
        and second.intercepted
        and third.intercepted
        and final.status == "allowed"
        and expected.issubset(kinds)
        and redacted
    )
    return {
        "ok": ok,
        "layer": "local-application-request-review-chain",
        "status": final.status,
        "attempts": final.attempt,
        "restart_count": final.restart_count,
        "events": kinds,
        "matched_rule_ids": final.matched_rule_ids,
        "placeholders": dict(PLACEHOLDER_CONTRACT),
        "redaction_verified": redacted,
        "state_path": str(state_path),
    }
