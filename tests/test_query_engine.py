from app.application.query_engine import GeoQueryEngine

engine = GeoQueryEngine()

queries = [
    "schools nearby",
    "hospital near city",
    "best place for factory",
    "مدرسة قريبة",
    "أفضل مكان لمول"
]

for q in queries:

    result = engine.query(q)

    print("=" * 50)
    print("QUESTION:", q)
    print(result)