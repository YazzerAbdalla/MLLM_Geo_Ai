class GeoQueryEngine:

    def __init__(self):

        self.patterns = {
            "education": [
                "school",
                "education",
                "university",
                "college",
                "مدرسة",
                "تعليم",
                "جامعة"
            ],

            "health": [
                "hospital",
                "clinic",
                "medical",
                "health",
                "مستشفى",
                "عيادة",
                "صحة"
            ],

            "commercial": [
                "shop",
                "mall",
                "market",
                "bank",
                "متجر",
                "مول",
                "بنك"
            ],

            "industrial": [
                "factory",
                "industry",
                "industrial",
                "مصنع",
                "صناعي"
            ],

            "recommendation": [
                "best place",
                "best location",
                "recommend",
                "أفضل مكان",
                "أفضل موقع",
                "اقترح"
            ]
        }

    # -------------------------
    # LANGUAGE DETECTION
    # -------------------------
    def detect_language(self, question: str):

        for ch in question:

            if "\u0600" <= ch <= "\u06FF":
                return "ar"

        return "en"

    # -------------------------
    # QUERY TYPE DETECTION
    # -------------------------
    def detect_query_type(self, question: str):

        q = question.lower()

        priority_order = [
            "recommendation",
            "education",
            "health",
            "commercial",
            "industrial"
        ]

        for query_type in priority_order:

            for keyword in self.patterns[query_type]:

                if keyword.lower() in q:
                    return query_type

        return "unknown"

    # -------------------------
    # MAIN QUERY
    # -------------------------
    def query(self, question: str):

        query_type = self.detect_query_type(
            question
        )

        lang = self.detect_language(
            question
        )

        rtl = lang == "ar"

        response = {
            "query_type": query_type,
            "language": lang,
            "rtl": rtl,
            "cell_ids": [],
            "explanation": "",
            "explanation_ar": ""
        }

        if query_type == "education":

            response["cell_ids"] = [
                "cell_001",
                "cell_002"
            ]

            response["explanation"] = (
                "Education related locations detected."
            )

            response["explanation_ar"] = (
                "تم اكتشاف مواقع مرتبطة بالتعليم."
            )

        elif query_type == "health":

            response["cell_ids"] = [
                "cell_010",
                "cell_011"
            ]

            response["explanation"] = (
                "Healthcare related locations detected."
            )

            response["explanation_ar"] = (
                "تم اكتشاف مواقع مرتبطة بالصحة."
            )

        elif query_type == "commercial":

            response["cell_ids"] = [
                "cell_020",
                "cell_021"
            ]

            response["explanation"] = (
                "Commercial locations detected."
            )

            response["explanation_ar"] = (
                "تم اكتشاف مواقع تجارية."
            )

        elif query_type == "industrial":

            response["cell_ids"] = [
                "cell_030",
                "cell_031"
            ]

            response["explanation"] = (
                "Industrial locations detected."
            )

            response["explanation_ar"] = (
                "تم اكتشاف مواقع صناعية."
            )

        elif query_type == "recommendation":

            response["cell_ids"] = [
                "cell_100"
            ]

            response["explanation"] = (
                "Recommended location found."
            )

            response["explanation_ar"] = (
                "تم العثور على موقع موصى به."
            )

        else:

            response["explanation"] = (
                "Query pattern not recognized."
            )

            response["explanation_ar"] = (
                "لم يتم التعرف على نوع الاستعلام."
            )

        return response