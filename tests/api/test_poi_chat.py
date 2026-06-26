import pytest
from app.application import poi_chat_service

SAMPLE_ANALYSIS = {
    "total_pois": 100,
    "area_km2": 2.5,
    "poi_density": 40.0,
    "top_categories": [
        {"category": "restaurant", "count": 30},
        {"category": "retail", "count": 20},
    ],
    "category_counts": {"restaurant": 30, "retail": 20},
    "reverse_geocoding": {
        "area_name": "Test City",
        "city": "Test",
        "country": "Testland",
    },
}

MOCK_SECTIONED_RESPONSE = (
    "Summary: This area contains 100 POIs with restaurants and retail dominating.\n"
    "Answer: Based on the available POI data, the area appears suitable for development."
)
MOCK_TEXT_RESPONSE = "Based on the available POI data, the area appears suitable for development."


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setattr(poi_chat_service, "GEMINI_API_KEY", "fake-test-key")
    monkeypatch.setattr(poi_chat_service, "_get_cached_summary", lambda h: None)
    monkeypatch.setattr(poi_chat_service, "_set_cached_summary", lambda h, s: None)


class TestPoiChatSuccess:
    def test_returns_plain_english_answers(self, client, monkeypatch):
        monkeypatch.setattr(
            poi_chat_service, "_call_gemini",
            lambda api_key, prompt: MOCK_SECTIONED_RESPONSE,
        )

        response = client.post("/api/v1/internal/poi-chat", json={
            "analysis": SAMPLE_ANALYSIS,
            "question": "Is this area suitable?",
        })

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "answer" in data
        assert data["model"] == "gemini-2.5-flash"

        assert "{" not in data["answer"]
        assert "}" not in data["answer"]
        assert data["summary"].startswith("This area")
        assert "100 POIs" in data["summary"]

    def test_summary_and_answer_are_strings(self, client, monkeypatch):
        monkeypatch.setattr(
            poi_chat_service, "_call_gemini",
            lambda api_key, prompt: MOCK_SECTIONED_RESPONSE,
        )

        response = client.post("/api/v1/internal/poi-chat", json={
            "analysis": SAMPLE_ANALYSIS,
            "question": "Is this area suitable?",
        })

        data = response.json()
        assert isinstance(data["summary"], str)
        assert isinstance(data["answer"], str)
        assert isinstance(data["model"], str)

    def test_with_history(self, client, monkeypatch):
        monkeypatch.setattr(
            poi_chat_service, "_call_gemini",
            lambda api_key, prompt: MOCK_SECTIONED_RESPONSE,
        )

        response = client.post("/api/v1/internal/poi-chat", json={
            "analysis": SAMPLE_ANALYSIS,
            "question": "What about healthcare?",
            "history": [
                {"role": "user", "content": "Summarize this area."},
                {"role": "assistant", "content": "It has 100 POIs."},
            ],
        })

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "summary" in data

    def test_empty_history_defaults_to_empty_list(self, client, monkeypatch):
        monkeypatch.setattr(
            poi_chat_service, "_call_gemini",
            lambda api_key, prompt: MOCK_SECTIONED_RESPONSE,
        )

        response = client.post("/api/v1/internal/poi-chat", json={
            "analysis": SAMPLE_ANALYSIS,
            "question": "Test?",
        })

        assert response.status_code == 200


class TestFollowUp:
    def test_follow_up_does_not_repeat_summary(self, client, monkeypatch):
        captured = {"prompts": []}

        def mock_gemini(api_key, prompt):
            captured["prompts"].append(prompt)
            return MOCK_SECTIONED_RESPONSE

        monkeypatch.setattr(poi_chat_service, "_call_gemini", mock_gemini)

        monkeypatch.setattr(
            poi_chat_service, "_get_cached_summary",
            lambda h: None,
        )

        def set_cache(h, s):
            def getter(hash_val):
                return s
            monkeypatch.setattr(
                poi_chat_service, "_get_cached_summary", getter,
            )

        monkeypatch.setattr(
            poi_chat_service, "_set_cached_summary", set_cache,
        )

        resp1 = client.post("/api/v1/internal/poi-chat", json={
            "analysis": SAMPLE_ANALYSIS,
            "question": "First question?",
        })
        assert resp1.status_code == 200

        resp2 = client.post("/api/v1/internal/poi-chat", json={
            "analysis": SAMPLE_ANALYSIS,
            "question": "Second question?",
        })
        assert resp2.status_code == 200

        d1 = resp1.json()
        d2 = resp2.json()

        assert d1["summary"] == d2["summary"]
        assert d1["summary"] != ""
        assert d2["answer"] != d1["answer"]

        prompt1 = captured["prompts"][0]
        prompt2 = captured["prompts"][1]
        assert "Summary" in prompt1
        assert "Summary" not in prompt2


class TestValidation:
    def test_empty_question(self, client):
        response = client.post("/api/v1/internal/poi-chat", json={
            "analysis": SAMPLE_ANALYSIS,
            "question": "",
        })
        assert response.status_code == 400

    def test_missing_analysis(self, client):
        response = client.post("/api/v1/internal/poi-chat", json={
            "question": "Test?",
        })
        assert response.status_code == 400

    def test_invalid_role_in_history(self, client):
        response = client.post("/api/v1/internal/poi-chat", json={
            "analysis": SAMPLE_ANALYSIS,
            "question": "Test?",
            "history": [{"role": "invalid_role", "content": "Hello"}],
        })
        assert response.status_code == 422


class TestHistoryTruncation:
    def test_history_truncated(self, client, monkeypatch):
        history = []
        for i in range(20):
            history.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message number {i}",
            })

        captured = {"prompt": None}

        def mock_gemini(api_key, prompt):
            captured["prompt"] = prompt
            return MOCK_SECTIONED_RESPONSE

        monkeypatch.setattr(poi_chat_service, "_call_gemini", mock_gemini)

        response = client.post("/api/v1/internal/poi-chat", json={
            "analysis": SAMPLE_ANALYSIS,
            "question": "Test?",
            "history": history,
        })

        assert response.status_code == 200
        prompt = captured["prompt"]
        assert prompt is not None

        assert "Message number 0" not in prompt
        assert "Message number 19" in prompt
        assert "Message number 10" in prompt


class TestGeminiErrors:
    def test_config_error(self, client, monkeypatch):
        monkeypatch.setattr(poi_chat_service, "GEMINI_API_KEY", "")

        response = client.post("/api/v1/internal/poi-chat", json={
            "analysis": SAMPLE_ANALYSIS,
            "question": "Test?",
        })
        assert response.status_code == 503

    def test_timeout_error(self, client, monkeypatch):
        def mock_fail(api_key, prompt):
            raise poi_chat_service.GeminiTimeoutError("Gemini request timed out")

        monkeypatch.setattr(poi_chat_service, "_call_gemini", mock_fail)

        response = client.post("/api/v1/internal/poi-chat", json={
            "analysis": SAMPLE_ANALYSIS,
            "question": "Test?",
        })
        assert response.status_code == 504

    def test_rate_limit_error(self, client, monkeypatch):
        def mock_fail(api_key, prompt):
            raise poi_chat_service.GeminiRateLimitError("Rate limit exceeded")

        monkeypatch.setattr(poi_chat_service, "_call_gemini", mock_fail)

        response = client.post("/api/v1/internal/poi-chat", json={
            "analysis": SAMPLE_ANALYSIS,
            "question": "Test?",
        })
        assert response.status_code == 429

    def test_invalid_request_error(self, client, monkeypatch):
        def mock_fail(api_key, prompt):
            raise poi_chat_service.GeminiInvalidRequestError("Invalid request")

        monkeypatch.setattr(poi_chat_service, "_call_gemini", mock_fail)

        response = client.post("/api/v1/internal/poi-chat", json={
            "analysis": SAMPLE_ANALYSIS,
            "question": "Test?",
        })
        assert response.status_code == 400

    def test_unknown_error(self, client, monkeypatch):
        def mock_fail(api_key, prompt):
            raise poi_chat_service.GeminiApiError("Unknown failure")

        monkeypatch.setattr(poi_chat_service, "_call_gemini", mock_fail)

        response = client.post("/api/v1/internal/poi-chat", json={
            "analysis": SAMPLE_ANALYSIS,
            "question": "Test?",
        })
        assert response.status_code == 500


class TestAnalysisValidation:
    def test_missing_required_field(self, client):
        bad_analysis = {
            "total_pois": 100,
            "area_km2": 2.5,
        }

        response = client.post("/api/v1/internal/poi-chat", json={
            "analysis": bad_analysis,
            "question": "Test?",
        })
        assert response.status_code == 400
        assert "missing required field" in response.json()["detail"]


class TestParseSummaryAnswer:
    def test_parses_sectioned_response(self):
        raw = (
            "Summary: This area has 50 restaurants and 30 retail stores.\n"
            "Answer: The area appears well-suited for commercial use."
        )
        summary, answer = poi_chat_service._parse_summary_answer(raw)
        assert summary == "This area has 50 restaurants and 30 retail stores."
        assert answer == "The area appears well-suited for commercial use."

    def test_fallback_when_summary_missing(self):
        raw = "Answer: Direct answer about the area."
        summary, answer = poi_chat_service._parse_summary_answer(raw)
        assert summary == ""
        assert answer == "Direct answer about the area."

    def test_fallback_when_answer_missing(self):
        raw = "Summary: Just a summary here."
        summary, answer = poi_chat_service._parse_summary_answer(raw)
        assert summary == "Just a summary here."
        assert answer == "Just a summary here."

    def test_fallback_when_no_sections(self):
        raw = "Just a plain answer without any sections."
        summary, answer = poi_chat_service._parse_summary_answer(raw)
        assert summary == ""
        assert answer == "Just a plain answer without any sections."
