Analyze the project using the following sources as primary context:

* Step 2 document
* Arabic onboarding/team distribution document
* Current reports inside the repository (especially progress, remaining phases, evaluation reports, and implementation status)

Your mission is to perform a complete implementation audit and progress validation for the project.

## Phase 1 — Extract Objectives & Expected Deliverables

First, analyze the Step 2 document and ai-tasks.md carefully.

Identify and extract:

* The objectives of each AI-related task
* The expected outputs/deliverables from students
* The required files, APIs, scripts, reports, metrics, datasets, and training artifacts
* The success criteria for every task
* The planned architecture and intended workflow

Before starting any implementation checks, summarize all AI tasks and objectives clearly so they can be used as execution context for the rest of the audit.

---

## Phase 2 — Inspect Current Codebase

Analyze the current repository implementation and compare it against:

* Step 2 objectives
* Onboarding document responsibilities
* Remaining phases report
* Planned AI pipeline

For every task:

* Verify whether the implementation exists
* Check whether it is complete, partial, missing, or broken
* Validate whether the implementation actually satisfies the original objective
* Detect placeholder logic, mock implementations, hardcoded values, or incomplete integrations
* Identify architectural mismatches between the plan and the actual implementation

Pay special attention to:

* AI training pipeline
* Dataset preparation
* Multi-class labeling
* Feature fusion
* OSMnx graph generation
* Evaluation metrics
* Ablation study support
* Training history tracking
* Spatial Accuracy implementation
* Validation monitoring
* API integration
* Model loading and inference stability

---

## Phase 3 — Validate AI Training & Evaluation

Inspect the AI training pipeline deeply.

The agent should:

* Verify dataset quality and class distribution
* Check whether the model training is meaningful or suffering from issues like single-class learning
* Validate train/validation splitting
* Verify loss tracking and evaluation logic
* Check whether saved weights are compatible with model definitions
* Verify embedding pipelines and encoder usage
* Validate evaluation metrics implementation
* Inspect generated artifacts and outputs

Then actually test the training/evaluation pipeline when possible.

The agent should:

* Run existing tests
* Run training/evaluation scripts
* Detect crashes or broken dependencies
* Validate generated outputs
* Confirm whether metrics are real and meaningful

---

## Phase 4 — Create Missing Tests

If test files, validation scripts, or evaluation utilities are missing:

* Create appropriate test files
* Add validation checks where necessary
* Add missing evaluation scripts
* Add smoke tests for critical AI pipeline components
* Run the created tests
* Document results and failures

---

## Phase 5 — Generate Comprehensive Audit Report

After completing all checks, generate a comprehensive technical report containing:

### 1. Planned Objectives

* What was originally required according to Step 2 and onboarding documents

### 2. Expected Deliverables

* What students were supposed to complete

### 3. Actual Implementation Status

For every task:

* Completed
* Partial
* Missing
* Broken
* Needs Refactor

### 4. AI Training Audit

Include:

* Dataset quality analysis
* Training pipeline validation
* Evaluation quality
* Model stability
* Metrics validation
* Ablation support
* Validation monitoring
* Training artifacts review

### 5. Test Results

Include:

* Existing tests discovered
* Newly created tests
* Test execution results
* Failures and crashes
* Missing coverage

### 6. Gap Analysis

Compare:

* Current implementation
  vs
* Step 2 objectives

Clearly identify:

* Missing requirements
* Incomplete phases
* Incorrect implementations
* Risks for defense/demo

### 7. Final Readiness Assessment

Provide:

* Overall completion percentage
* AI pipeline readiness
* Demo readiness
* Defense readiness
* Critical blockers
* Recommended next priorities

---

Important instructions:

* Do not assume features are complete unless verified in code
* Prefer evidence from implementation over comments/documentation
* Use the Step 2 document as the primary source of truth
* Validate functionality practically whenever possible
* Distinguish clearly between:

  * implemented
  * partially implemented
  * planned only
  * mocked/stubbed
  * broken
* Focus heavily on AI-related tasks, training quality, and evaluation correctness
* Produce evidence-based findings only
