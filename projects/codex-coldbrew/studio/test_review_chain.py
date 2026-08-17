# -*- coding: utf-8 -*-
from __future__ import annotations

import itertools
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import review_chain as review


class ReviewChainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp.name) / "review-state.json"
        self.event_ids = itertools.count(1)
        self.clock_ticks = itertools.count(0)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def clock(self) -> datetime:
        return datetime(2026, 8, 8, 0, 0, next(self.clock_ticks), tzinfo=timezone.utc)

    def event_id(self) -> str:
        return f"event-{next(self.event_ids)}"

    def rules(self) -> list[dict[str, object]]:
        return [
            {
                "rule_id": "chat-review",
                "endpoint_pattern": r"/v1/chat/completions$",
                "methods": ["POST"],
                "body_keys_all": ["messages", "metadata"],
                "body_pattern": "需要审查|review-me",
                "header_names_all": ["authorization"],
                "review_flag": "MANUAL_REVIEW",
                "priority": 20,
            },
            {
                "rule_id": "disabled-rule",
                "endpoint_pattern": ".*",
                "review_flag": "DISABLED",
                "priority": 100,
                "enabled": False,
            },
        ]

    def adapter(self) -> review.ReviewChainAdapter:
        return review.ReviewChainAdapter(
            self.state_path,
            self.rules(),
            clock=self.clock,
            event_id_factory=self.event_id,
        )

    def request(self) -> review.OutboundRequest:
        return review.OutboundRequest(
            request_id="request-1",
            session_id="session-1",
            method="post",
            endpoint="https://HOST/v1/chat/completions?access_token=QUERY_TOKEN_SECRET",
            headers={
                "Authorization": "Bearer HEADER_TOKEN_SECRET",
                "Content-Type": "application/json",
            },
            body={
                "messages": [{"role": "user", "content": "需要审查的中文请求 BODY_SECRET_TEXT"}],
                "metadata": {"token": "BODY_TOKEN_SECRET"},
            },
        )

    def test_fixture_proves_matching_request_enters_review_chain(self) -> None:
        adapter = self.adapter()
        request = self.request()
        decision = adapter.intercept(request)

        self.assertTrue(decision.intercepted)
        self.assertEqual(decision.status, "awaiting_review")
        self.assertEqual(decision.matched_rule_ids, ("chat-review",))
        self.assertEqual(
            set(decision.contract or {}),
            {review.REVIEW_ENDPOINT, review.REQUEST_BODY, review.REVIEW_FLAG},
        )
        self.assertEqual(decision.contract[review.REVIEW_ENDPOINT], review.REVIEW_ENDPOINT)
        self.assertEqual(decision.contract[review.REQUEST_BODY], request.body)
        self.assertEqual(decision.contract[review.REVIEW_FLAG], "MANUAL_REVIEW")

        state = adapter.state
        self.assertIsNotNone(state)
        self.assertEqual([event.kind for event in state.events], ["request", "hit", "review_request"])
        self.assertEqual(state.events[0].attempt, 1)
        self.assertEqual(state.events[1].rule_ids, ("chat-review",))

        persisted = self.state_path.read_text(encoding="utf-8")
        json.loads(persisted)
        self.assertIn("需要审查", decision.contract[review.REQUEST_BODY]["messages"][0]["content"])
        for secret in (
            "QUERY_TOKEN_SECRET",
            "HEADER_TOKEN_SECRET",
            "BODY_SECRET_TEXT",
            "BODY_TOKEN_SECRET",
        ):
            self.assertNotIn(secret, persisted)
        self.assertNotIn("access_token=", persisted)

    def test_configurable_rules_can_bypass_without_dispatch_contract(self) -> None:
        adapter = self.adapter()
        request = review.OutboundRequest(
            request_id="request-bypass",
            session_id="session-1",
            method="GET",
            endpoint="https://HOST/v1/models",
            body={"query": "public"},
        )
        decision = adapter.intercept(request)
        self.assertFalse(decision.intercepted)
        self.assertIsNone(decision.contract)
        self.assertEqual(decision.status, "bypassed")
        self.assertEqual([event.kind for event in adapter.state.events], ["request", "bypass"])

    def test_response_flag_interrupt_and_retry_events_are_persisted(self) -> None:
        adapter = self.adapter()
        request = self.request()
        adapter.intercept(request)

        state = adapter.record_response(request.request_id, "RETRY")
        self.assertEqual(state.status, "retry_pending")
        decision = adapter.retry(request)
        self.assertEqual(decision.status, "awaiting_review")
        self.assertEqual(adapter.state.attempt, 2)

        state = adapter.interrupt(request.request_id, "local-cancel")
        self.assertEqual(state.status, "interrupted")
        adapter.retry(request)
        state = adapter.record_response(request.request_id, "ALLOW")
        self.assertEqual(state.status, "allowed")
        self.assertIsNone(state.active_request_id)
        self.assertEqual(state.review_flag, "ALLOW")

        kinds = [event.kind for event in state.events]
        self.assertEqual(kinds.count("request"), 3)
        self.assertEqual(kinds.count("retry"), 2)
        self.assertIn("response", kinds)
        self.assertIn("interrupted", kinds)
        self.assertEqual(state.attempt, 3)

    def test_restart_recovery_requires_full_request_resubmission(self) -> None:
        first = self.adapter()
        request = self.request()
        first.intercept(request)

        restarted = self.adapter()
        loaded = restarted.state
        self.assertEqual(loaded.status, "awaiting_review")
        self.assertEqual(loaded.attempt, 1)

        recovered = restarted.recover(request.session_id)
        self.assertEqual(recovered.status, "retry_pending")
        self.assertEqual(recovered.restart_count, 1)
        self.assertEqual(recovered.events[-1].kind, "recovered")
        self.assertEqual(recovered.events[-1].details["previous_status"], "awaiting_review")

        decision = restarted.retry(request)
        self.assertTrue(decision.intercepted)
        restarted.record_response(request.request_id, "APPROVED")

        reloaded = self.adapter().state
        self.assertEqual(reloaded.status, "allowed")
        self.assertEqual(reloaded.attempt, 2)
        self.assertIn("recovered", [event.kind for event in reloaded.events])
        persisted = self.state_path.read_text(encoding="utf-8")
        self.assertNotIn("BODY_SECRET_TEXT", persisted)
        self.assertNotIn("HEADER_TOKEN_SECRET", persisted)

    def test_unmapped_response_flag_and_overlapping_request_are_rejected(self) -> None:
        adapter = self.adapter()
        request = self.request()
        adapter.intercept(request)
        with self.assertRaises(review.ReviewChainError):
            adapter.record_response(request.request_id, "UNKNOWN")
        with self.assertRaises(review.StateConflictError):
            adapter.intercept(
                review.OutboundRequest(
                    request_id="request-2",
                    session_id=request.session_id,
                    method="POST",
                    endpoint="https://HOST/v1/chat/completions",
                    body={"messages": [], "metadata": {}},
                    headers={"Authorization": "Bearer OTHER_SECRET"},
                )
            )

    def test_placeholder_contract_is_stable(self) -> None:
        self.assertEqual(
            review.PLACEHOLDER_CONTRACT,
            {
                "endpoint": "REVIEW_ENDPOINT",
                "body": "REQUEST_BODY",
                "flag": "REVIEW_FLAG",
            },
        )

    def test_self_test_covers_hit_interrupt_retry_restart_and_allow(self) -> None:
        result = review.run_self_test(Path(self.temp.name) / "fixture")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["status"], "allowed")
        self.assertEqual(result["attempts"], 3)
        self.assertEqual(result["restart_count"], 1)
        self.assertTrue(result["redaction_verified"])
        for kind in ("hit", "interrupted", "retry", "recovered", "response"):
            self.assertIn(kind, result["events"])


if __name__ == "__main__":
    unittest.main()
