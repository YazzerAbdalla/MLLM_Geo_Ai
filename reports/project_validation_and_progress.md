# MLLM-Geo-AI Urban AI Dashboard

## Project Validation & Progress Report

### Date: June 2026

---

# Executive Summary

The Urban AI Dashboard has successfully completed a major validation and stabilization phase. Core backend services, POI processing, multimodal classification workflows, model inference, and data pipelines have been audited and tested.

During this phase, several critical issues were discovered, including missing POI feature generation, classifier checkpoint loading failures, graph modality training gaps, and dataset label leakage. These issues were investigated through code audits, runtime validations, retraining experiments, and end-to-end testing.

The classification system is now operational with trained model checkpoints successfully loaded during inference, non-zero POI embeddings being generated, and meaningful classification outputs being produced.

---

# 1. Backend & Infrastructure Status

## API Layer

Status: Completed

Validated endpoints:

* Area loading workflow
* Grid generation
* Classification requests
* Job tracking
* Result retrieval
* Thumbnail serving

Results:

* API endpoints operational
* Celery task execution verified
* SQLite persistence functioning
* GeoJSON result generation validated

---

## Celery & Background Processing

Status: Completed

Validated:

* Task dispatch
* Worker execution
* Job status updates
* Result persistence

Findings:

* Classification tasks execute successfully
* Results correctly stored and retrievable
* No blocking issues detected

---

# 2. POI Pipeline Validation

## Initial Issue

Historical classification outputs contained:

* text_embedding_norm = 0.0
* poi_top_categories = []

This indicated that the POI modality was not contributing to classification.

## Root Cause

Investigation confirmed that older versions of:

tasks/load_area.py

did not populate:

* text_des
* poi_count

before storing generated grids.

As a result:

* POI embeddings were never generated
* Zero vectors propagated through classification

## Resolution

POI processing was added to the area loading workflow.

Current validation shows:

* Non-empty text_des fields
* Non-zero embedding vectors
* Valid POI categories
* Successful embedding generation

Status: Fixed

---

# 3. Embedding Model Validation

Model:

paraphrase-multilingual-MiniLM-L12-v2

Validation Results:

| Test                   | Result |
| ---------------------- | ------ |
| Model Loading          | PASS   |
| Embedding Generation   | PASS   |
| Arabic Text Processing | PASS   |
| Non-Zero Embeddings    | PASS   |

Observed Runtime:

* Model loads successfully
* Average embedding norm: 3.0–4.0
* Arabic POI descriptions processed correctly

Status: Operational

---

# 4. Classification Model Validation

## Original Issue

The inference pipeline instantiated:

UrbanMLP()

without loading trained weights.

Result:

* Random initialization
* Nearly uniform probabilities (~0.33)
* Unreliable predictions

## Resolution

Added checkpoint loading during classifier initialization.

Checkpoint:

models/urban_mlp.pt

Current Status:

* Trained weights loaded successfully
* Predictions no longer uniform
* Confidence scores realistic

Status: Fixed

---

# 5. Model Retraining Results

Dataset Size:

1,166 samples

Class Distribution:

| Class       | Samples |
| ----------- | ------- |
| Residential | 971     |
| Commercial  | 184     |
| Industrial  | 11      |

Training Outcome:

| Metric              | Value |
| ------------------- | ----- |
| Training Accuracy   | 100%  |
| Validation Accuracy | 100%  |
| Test Accuracy       | 100%  |
| Weighted F1         | 100%  |
| Macro F1            | 100%  |

Important Note:

The perfect metrics were later determined to be misleading due to label leakage within the dataset.

---

# 6. Multimodal Coverage Audit

## POI Modality

Coverage:

100%

Status:

Operational

---

## Satellite Imagery

Coverage:

144 / 1166 samples

12.3%

Status:

Partially Available

Limitation:

Most training samples contain zero image features due to missing imagery.

---

## Graph Features

Coverage:

0% during training

Status:

Not Used During Training

Root Cause:

Training scripts used hardcoded values:

* [0,0,0]
* [2,1,0]

instead of real road-network features.

However:

The inference pipeline correctly computes real graph features.

Infrastructure exists but is disconnected from training.

---

# 7. Label Leakage Audit

Severity:

CRITICAL

Investigation confirmed deterministic label generation.

Current mapping:

Education → Residential

Health → Residential

Bank → Commercial

Mall → Commercial

Industrial → Industrial

Implemented in:

scripts/relabel_dataset.py

Because labels are directly derived from category values, the model learns category-to-label shortcuts rather than genuine urban classification behavior.

Audit Results:

* Cramer's V = 1.0
* Chi-Square p-value ≈ 0
* Perfect category-label correlation

Impact:

* Reported accuracy metrics are not representative of real-world performance.
* Model evaluation is artificially inflated.

Status:

Confirmed

---

# 8. Current Classification Quality

After fixes:

Example outputs show:

* Commercial zones predicted with >99% confidence
* Residential zones predicted with >99% confidence
* Non-zero POI embeddings
* Meaningful category extraction

Classification pipeline now functions correctly from a software engineering perspective.

However:

Model quality remains limited by dataset quality and label leakage.

---

# 9. Frontend Integration Status

Current Status:

In Progress

Remaining Work:

* API integration with frontend
* Classification result visualization
* Job progress updates
* Map interaction workflows
* End-to-end UI testing

Priority:

HIGH

Required before project demonstration.

---

# 10. Risks Before Defense

## High Risk

Dataset label leakage.

Impact:

Academic reviewers may challenge model validity if not properly disclosed.

Mitigation:

Present this as a known limitation and future work item.

---

## Medium Risk

Graph modality not used during training.

Impact:

System is not fully multimodal despite supporting multimodal inference.

Mitigation:

Document as future enhancement.

---

## Medium Risk

Limited satellite imagery coverage.

Impact:

Image modality contributes minimally during training.

Mitigation:

State dataset limitations.

---

# 11. Recommendations for Final Submission

Given the remaining timeline:

### Before Book Submission

* Freeze architecture
* Finish frontend integration
* Update system diagrams
* Document dataset limitations
* Document leakage findings transparently

### Before Defense

Focus on:

1. Stable demonstration
2. End-to-end workflow
3. Architecture explanation
4. Engineering achievements
5. Future improvements

Avoid major retraining or architectural refactoring.

---

# Overall Project Status

| Component                 | Status      |
| ------------------------- | ----------- |
| Backend APIs              | Complete    |
| Celery Tasks              | Complete    |
| Grid Generation           | Complete    |
| POI Pipeline              | Complete    |
| Classification Pipeline   | Complete    |
| Checkpoint Loading        | Complete    |
| Model Retraining          | Complete    |
| Runtime Validation        | Complete    |
| Frontend Integration      | In Progress |
| Dataset Quality Review    | Complete    |
| Label Leakage Audit       | Complete    |
| Documentation             | In Progress |
| Final Defense Preparation | In Progress |

Overall Completion Estimate: 85–90%

The system is functionally operational and suitable for demonstration, with remaining effort focused primarily on frontend integration, documentation finalization, and presentation preparation.
