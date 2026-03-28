# GEMINI.md - Custom MLLM-Geo-AI (Enterprise Edition)

## 🌍 App Description
A production-ready FastAPI application for **Urban Classification** using Domain-Driven Design (DDD). The system processes POI data via an MLLM-Geo-AI engine to categorize Cairo's urban fabric.

## 🏗 Architectural Patterns
- **Architecture:** Domain-Driven Design (DDD) - (Domain, Application, Infrastructure, Interface).
- **Development Cycle:** Test-Driven Development (TDD). **RED-GREEN-REFACTOR** (Tests first, implementation second).
- **API Framework:** FastAPI.

---

## 🎭 Agent Roles & Protocols

/******
 * @role **SYSTEM_RELIABILITY_ENGINEER**
 * @description Manages environment, dependencies, and virtual environment integrity.
 * @protocols
 * 1. Check for Python 3.10+ and existing `.venv`. 
 * 2. Create and activate virtual environment if not present.
 * 3. Manage `requirements.txt` ensuring all spatial and AI libs are locked.
 ******/

/******
 * @role **DDD_TECHNICAL_ARCHITECT**
 * @description Enforces the Domain-Driven Design structure.
 * @protocols
 * 1. Maintain clear separation: 
 * - `Domain`: Entities (GridCell, POI) and Value Objects.
 * - `Application`: Use Cases (ClassifyUrbanArea).
 * - `Infrastructure`: Repositories (CSVLoader, AIModelLoader).
 * - `Interfaces`: FastAPI Controllers/Routes.
 * 2. All business logic MUST reside in the Domain layer.
 ******/

/******
 * @role **QA_AUTOMATION_LEAD**
 * @description Enforces the Test-Driven Development (TDD) cycle.
 * @protocols
 * 1. FORBID any feature implementation before a failing test is written in `/tests`.
 * 2. Use `pytest` for unit and integration testing.
 * 3. Verify spatial calculations and AI inference outputs against expected mock results.
 ******/

---

## 🛠 Tech Stack
- **Backend:** FastAPI, Uvicorn.
- **AI Core:** Sentence-Transformers, Scikit-learn.
- **Geospatial:** GeoPandas, Shapely.
- **Testing:** Pytest, HTTPX.