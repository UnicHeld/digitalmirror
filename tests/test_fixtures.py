"""Valida contratos e coerência dos oráculos; não implementa o motor de produção."""

import copy
import json
import unittest
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "specs/001-foundation/contracts/fixtures.schema.json").read_text())
FIXTURES = json.loads((ROOT / "tests/fixtures/workday-cases.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


def check_fixture_integrity(document):
    VALIDATOR.validate(document)
    ids = [case["id"] for case in document["cases"]]
    if len(ids) != len(set(ids)):
        raise ValueError("ID de caso duplicado")
    for case in document["cases"]:
        policy = case["policy"]
        zone = ZoneInfo(policy["timezone"])

        def local(clock, date=policy["date"], timezone=zone):
            return datetime.fromisoformat(date + "T" + clock).replace(tzinfo=timezone)

        start, end = local(policy["start"]), local(policy["end"])
        lunch_start, lunch_end = local(policy["lunch_start"]), local(policy["lunch_end"])
        if not start < lunch_start < lunch_end < end:
            raise ValueError("Almoço fora da jornada")
        if (lunch_end - lunch_start).total_seconds() != 3600:
            raise ValueError("Almoço padrão precisa de uma hora")
        as_of = datetime.fromisoformat(case["as_of"])
        windows = [(start, lunch_start), (lunch_end, end)]
        elapsed = sum(max(0, (min(b, as_of) - a).total_seconds()) for a, b in windows)
        states = defaultdict(float)
        apps = defaultdict(float)
        tabs = defaultdict(float)
        external = 0
        previous = None
        for item in case["intervals"]:
            a, b = datetime.fromisoformat(item["start"]), datetime.fromisoformat(item["end"])
            if a >= b or (previous is not None and a < previous) or b > as_of:
                raise ValueError("Intervalo invertido, sobreposto ou futuro")
            previous = b
            seconds = sum(
                max(0, (min(b, wb, as_of) - max(a, wa)).total_seconds()) for wa, wb in windows
            )
            states[item["state"]] += seconds
            external += max(0, (b - max(a, end)).total_seconds())
            if item["state"] in ("ACTIVE", "LOW_ACTIVITY", "IDLE"):
                apps[item["app"] or "unknown"] += seconds
                if item["tab"]:
                    if item["app"] != "browser":
                        raise ValueError("Aba fora do browser")
                    tabs[item["tab"]] += seconds
            elif item["app"] is not None or item["tab"] is not None:
                raise ValueError("Estado sem presença atribui foco")
            if item["state"] == "UNKNOWN" and item["quality"] != "unknown":
                raise ValueError("Gap com qualidade incorreta")
        expected = case["expected"]
        if elapsed != expected["elapsed_seconds"] or sum(states.values()) != elapsed:
            raise ValueError("Fixture não cobre a jornada decorrida")
        if any(states[s] != value for s, value in expected["state_seconds"].items()):
            raise ValueError("Estados não reconciliam")
        if dict(apps) != expected["app_seconds"] or dict(tabs) != expected["tab_seconds"]:
            raise ValueError("Foco não reconcilia")
        if external != expected["external_seconds"]:
            raise ValueError("Tempo externo não reconcilia")
        presence = sum(expected["state_seconds"][s] for s in ("ACTIVE", "LOW_ACTIVITY", "IDLE"))
        observed = presence + states["LOCKED"] + states["SUSPENDED"]
        if presence != expected["presence_seconds"] or observed != expected["observed_seconds"]:
            raise ValueError("P/O não reconciliam")
        ratios = {
            "presence_pct": (presence, elapsed),
            "coverage_pct": (observed, elapsed),
            "recent_interaction_pct": (states["ACTIVE"], presence),
            "daily_progress_pct": (presence, expected["daily_seconds"]),
        }
        for name, (numerator, denominator) in ratios.items():
            actual = expected[name]
            if denominator == 0:
                if actual is not None:
                    raise ValueError("Divisor zero precisa de N/A")
            elif actual is None or abs(actual - 100 * numerator / denominator) > 1e-9:
                raise ValueError("Percentual esperado inconsistente")


class FixtureTests(unittest.TestCase):
    def test_schema_and_all_examples(self):
        Draft202012Validator.check_schema(SCHEMA)
        check_fixture_integrity(FIXTURES)
        self.assertEqual(len(FIXTURES["cases"]), 16)

    def test_product_example(self):
        expected = FIXTURES["cases"][0]["expected"]
        self.assertEqual(expected["presence_seconds"], 450 * 60)
        self.assertEqual(expected["presence_pct"], 93.75)
        self.assertEqual(expected["coverage_pct"], 100)
        self.assertEqual(expected["recent_interaction_pct"], 80)

    def test_privacy_and_schema_reject_invalid_data(self):
        for key, value in (("title", "synthetic"), ("url", "https://work.example/path")):
            with self.subTest(key=key):
                document = copy.deepcopy(FIXTURES)
                document["cases"][0]["intervals"][0][key] = value
                with self.assertRaises(ValidationError):
                    check_fixture_integrity(document)
        for key, value in (("state", "OFF"), ("start", "2026-01-12T09:00:00")):
            document = copy.deepcopy(FIXTURES)
            document["cases"][0]["intervals"][0][key] = value
            with self.assertRaises(ValidationError):
                check_fixture_integrity(document)

    def test_negative_durations_overlap_lunch_and_totals(self):
        for mutation in ("inverted", "overlap", "lunch", "total", "duplicate"):
            with self.subTest(mutation=mutation):
                document = copy.deepcopy(FIXTURES)
                case = document["cases"][0]
                if mutation == "inverted":
                    case["intervals"][0]["end"] = case["intervals"][0]["start"]
                elif mutation == "overlap":
                    case["intervals"][1]["start"] = case["intervals"][0]["start"]
                elif mutation == "lunch":
                    case["policy"]["lunch_end"] = "14:00"
                elif mutation == "duplicate":
                    document["cases"][1]["id"] = case["id"]
                else:
                    case["expected"]["presence_seconds"] += 1
                with self.assertRaises(ValueError):
                    check_fixture_integrity(document)

    def test_every_requirement_has_owner(self):
        text = (ROOT / "docs/requirements.md").read_text()
        for prefix, count in (("RF", 16), ("RNF", 10)):
            for number in range(1, count + 1):
                self.assertRegex(text, rf"\| {prefix}-{number:02d} \| EP-\d{{2}} \|")
