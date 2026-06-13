from app.application.query_engine import GeoQueryEngine

engine = GeoQueryEngine()


def run_test(question):

    print("=" * 60)
    print("QUESTION:", question)

    result = engine.query(question)

    print(result)

    return result


# --------------------------------------------------
# TEST 1 - English Query
# --------------------------------------------------

result = run_test(
    "schools nearby"
)

assert result["query_type"] == "education"
assert result["language"] == "en"
assert result["rtl"] is False


# --------------------------------------------------
# TEST 2 - Arabic Query
# --------------------------------------------------

result = run_test(
    "مدرسة قريبة"
)

assert result["query_type"] == "education"
assert result["language"] == "ar"
assert result["rtl"] is True


# --------------------------------------------------
# TEST 3 - Recommendation Query
# --------------------------------------------------

result = run_test(
    "best place for factory"
)

assert result["query_type"] == "recommendation"


# --------------------------------------------------
# TEST 4 - Empty Query (Empty Grid Placeholder)
# --------------------------------------------------

result = run_test(
    ""
)

assert result["query_type"] == "unknown"


# --------------------------------------------------
# TEST 5 - Zero Results / Unknown Query
# --------------------------------------------------

result = run_test(
    "space rocket launch zone"
)

assert result["query_type"] == "unknown"


print("\nAI-18 + AI-20 TESTS PASSED")