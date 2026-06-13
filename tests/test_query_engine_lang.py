from app.application.query_engine import GeoQueryEngine

engine = GeoQueryEngine()

questions = [
    "schools nearby",
    "hospital near city",
    "best place for factory",
    "مدرسة قريبة",
    "أفضل مكان لمول"
]

for q in questions:

    print("=" * 50)
    print("QUESTION:", q)

    result = engine.query(q)

    print(result)