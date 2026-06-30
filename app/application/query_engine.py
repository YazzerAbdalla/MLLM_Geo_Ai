import numpy as np


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
    # KEYWORD MATCHING
    # -------------------------
    def _keywords_match(self, categories, keywords):

        if not categories:
            return False

        cats_lower = [str(c).lower() for c in categories]

        for kw in keywords:

            kw_lower = kw.lower()

            for cat in cats_lower:

                if kw_lower in cat or cat in kw_lower:
                    return True

        return False

    # -------------------------
    # MAIN QUERY
    # -------------------------
    def query(self, question: str, classification_results=None, grid_gdf=None):

        query_type = self.detect_query_type(question)

        lang = self.detect_language(question)

        keywords = self.patterns.get(query_type, [])

        matched_cells = []

        # Unknown query type — return early with no matches
        if query_type == "unknown":

            answer = self._build_answer(query_type, 0, None, [], lang)

            return {
                "answer": answer,
                "query_type": query_type,
                "confidence": None,
                "matched_cells": [],
            }

        # ==================================================
        # MODE A — Classification results exist
        # ==================================================

        if classification_results:

            confidences = []

            for feature in classification_results:

                props = feature.get("properties", {})

                cell_id = props.get("cell_id")
                dominant_class = props.get("dominant_class", "")
                confidence = props.get("confidence", 0.0)
                centroid_raw = props.get("centroid")
                road_density = props.get("road_density")
                poi_categories = props.get("poi_top_categories", [])

                # Check if cell matches query

                match = False

                dominant_lower = dominant_class.lower()

                if dominant_lower == query_type:
                    match = True

                if not match and keywords:
                    if self._keywords_match(poi_categories, keywords):
                        match = True

                if match:

                    if isinstance(centroid_raw, tuple):
                        centroid_raw = list(centroid_raw)

                    matched_cells.append({
                        "cell_id": str(cell_id) if cell_id is not None else "",
                        "dominant_class": dominant_class,
                        "confidence": float(confidence),
                        "centroid": centroid_raw if centroid_raw else [0.0, 0.0],
                        "road_density": float(road_density) if road_density is not None else None,
                        "poi_categories": list(poi_categories) if isinstance(poi_categories, list) else []
                    })

                    confidences.append(float(confidence))

            avg_confidence = float(np.mean(confidences)) if confidences else 0.0

        # ==================================================
        # MODE B — Fallback to grid GeoDataFrame
        # ==================================================

        elif grid_gdf is not None and hasattr(grid_gdf, "iterrows"):

            for _, row in grid_gdf.iterrows():

                poi_categories = row.get("poi_categories")

                if poi_categories is None:
                    poi_categories = []

                if not isinstance(poi_categories, list):
                    try:
                        poi_categories = list(poi_categories)
                    except Exception:
                        poi_categories = []

                if keywords:
                    if not self._keywords_match(poi_categories, keywords):
                        continue

                centroid_geom = (
                    row.geometry.centroid
                    if hasattr(row.geometry, "centroid")
                    else None
                )

                centroid = (
                    [float(centroid_geom.x), float(centroid_geom.y)]
                    if centroid_geom is not None
                    else [0.0, 0.0]
                )

                matched_cells.append({
                    "cell_id": str(row.get("cell_id", "")),
                    "dominant_class": None,
                    "confidence": None,
                    "centroid": centroid,
                    "road_density": None,
                    "poi_categories": poi_categories
                })

            avg_confidence = None

        # ==================================================
        # NO DATA
        # ==================================================

        else:

            avg_confidence = None

        # ==================================================
        # BUILD ANSWER
        # ==================================================

        answer = self._build_answer(
            query_type,
            len(matched_cells),
            avg_confidence,
            matched_cells,
            lang
        )

        return {
            "answer": answer,
            "query_type": query_type,
            "confidence": avg_confidence,
            "matched_cells": matched_cells,
        }

    # -------------------------
    # ANSWER GENERATION
    # -------------------------
    def _build_answer(self, query_type, num_matched, avg_confidence, matched_cells, lang):

        if query_type == "unknown":
            if lang == "ar":
                return "لم يتم التعرف على نوع الاستعلام. يرجى طرح سؤال يتعلق بالتعليم أو الصحة أو المناطق التجارية أو الصناعية."
            return "Query pattern not recognized. Try asking about education, health, commercial, or industrial areas."

        if num_matched == 0:

            labels = {
                "education": "تعليمية" if lang == "ar" else "education",
                "health": "صحية" if lang == "ar" else "health",
                "commercial": "تجارية" if lang == "ar" else "commercial",
                "industrial": "صناعية" if lang == "ar" else "industrial",
                "recommendation": "موصى بها" if lang == "ar" else "recommended",
            }

            label = labels.get(query_type, query_type)

            if lang == "ar":
                return f"لم يتم العثور على مواقع {label} في هذه المنطقة."
            return f"No {label} locations found in this area."

        # Classification mode
        if avg_confidence is not None:

            conf_pct = round(float(avg_confidence) * 100)

            if lang == "ar":

                types_ar = {
                    "education": "تعليمية",
                    "health": "صحية",
                    "commercial": "تجارية",
                    "industrial": "صناعية",
                    "recommendation": "موصى بها",
                }

                answer = f"تم العثور على {num_matched} مواقع {types_ar.get(query_type, query_type)}. متوسط ثقة النموذج: {conf_pct}%."

            else:
                answer = f"Found {num_matched} {query_type} cells. Average model confidence: {conf_pct}%."

        # Fallback mode
        else:

            if lang == "ar":

                types_ar = {
                    "education": "تعليمية",
                    "health": "صحية",
                    "commercial": "تجارية",
                    "industrial": "صناعية",
                    "recommendation": "موصى بها",
                }

                answer = f"تم العثور على {num_matched} مواقع {types_ar.get(query_type, query_type)} في منطقة الشبكة."

            else:
                answer = f"Found {num_matched} {query_type} locations in the grid area."

        # Append top POI categories
        top_pois = self._collect_top_pois(matched_cells)

        if top_pois:

            if lang == "ar":
                answer += "\nأهم فئات الاهتمام:\n- " + "\n- ".join(top_pois)
            else:
                answer += "\nTop detected POI categories:\n- " + "\n- ".join(top_pois)

        return answer

    def _collect_top_pois(self, matched_cells, limit=5):

        seen = set()
        top = []

        for cell in matched_cells:

            for cat in cell.get("poi_categories", []):

                cat_str = str(cat).strip()

                if cat_str and cat_str not in seen:
                    seen.add(cat_str)
                    top.append(cat_str)

        return top[:limit]
