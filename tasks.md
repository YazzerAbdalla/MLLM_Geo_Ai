# Project Tasks

This file tracks the status of all project features and work.

**Last Updated**: May 2026  
**For**: Junior developers

---

## Format

- [x] = Completed
- [ ] = Not yet done

---

## Completed

### Documentation
- [x] docs/project_status.md - System status guide
- [x] docs/quick_start_demo.md - First run guide  
- [x] docs/file_status.md - File classification
- [x] docs/windows_setup_guide.md - Windows troubleshooting

### API Stabilization
- [x] Async task import guard in api.py
- [x] HTTP 501 responses for unimplemented endpoints
- [x] Clear error messages with documentation references

### Research Materials
- [x] docs/research/arabic/ - Arabic documentation folder

---

## Completed — AI Tasks

### Student 3 — Data / Dataset
- [x] AI-1: Re-label data/raw/project.csv and handle missing classes -> Complete
- [x] AI-2: Verify data_loader.py reads 'label' correctly -> Complete
- [x] AI-3: Write scripts/verify_dataset.py verification script -> Complete

### Student 4 — Training Pipeline
- [x] AI-4: Fix train_multimodal.py line 27 (poi_enc.encode -> embed_texts) -> Complete
- [x] AI-5: Change mlp_model.py hidden_dim=256 -> 128 & retrain -> Complete
- [x] AI-6: Add validation loop & history JSON in train_multimodal.py -> Complete
- [x] AI-8: Add --modalities flag for ablation studies in training -> Complete

### Student 5 — Evaluation
- [x] AI-9: Add norm fields in fusion_service.py -> Complete
- [x] AI-10: Implement 8-neighbor Spatial Accuracy in eval_multimodal.py -> Complete
- [x] AI-11: Run 3 ablation experiments and save CSVs in evals/ablation_results/ -> Complete

## Pending

### Student 4 — Training Pipeline
- [ ] AI-7: Pre-download Cairo road network (data/raw/roads.graphml)

### General Documentation
- [ ] Rewrite README.md with full setup
- [ ] Create docs/advanced_workflows.md
- [ ] Create docs/docker_deployment.md (optional)

### .gitignore
- [ ] Update .gitignore with comprehensive exclusions

### Cleanup
- [ ] Mark `manual_golden_run.py` as archive candidate
- [ ] Review `celery_app.py` status

---

## Future / Planned

These features are planned for future implementation:

### AI/ML Features
- [ ] Full training pipeline documentation
- [ ] Model evaluation scripts
- [ ] Hyperparameter tuning

### API Features
- [ ] Async task pipeline (Celery) - tasks/ module
- [ ] Natural language query (v2)
- [ ] WebSocket progress updates
- [ ] Redis job tracking (when Redis available)

### Data Features
- [ ] Real satellite imagery from GEE
- [ ] Large-scale processing
- [ ] Database integration

### Infrastructure
- [ ] Docker deployment (optional)
- [ ] Kubernetes deployment (optional)

---

## Feature Priority Order

### Priority 1: Onboarding (NOW)
- Clear documentation ✓
- Working quick start ✓
- File classification ✓

### Priority 2: Basic Functionality (SOON)
- Working synchronous classification
- Test improvements
- Better error messages

### Priority 3: Enhanced Features (LATER)
- Async pipeline
- Real data integration
- Advanced workflows

### Priority 4: Production (FUTURE)
- Docker deployment
- Monitoring
- Scaling

---

## How to Use This File

### For Learning What's Available
1. Read this file to see what's done
2. Check docs/project_status.md for system state
3. Check docs/file_status.md to find files

### For Contributing
1. Pick a "Pending" item
2. Coordinate with team
3. Implement carefully
4. Update this file

---

## Questions?

- If confused: Start with docs/quick_start_demo.md
- If blocked: Check docs/project_status.md  
- If wrong file: Check docs/file_status.md

---

## Summary

| Category | Count |
|----------|-------|
| Completed | 14 (7 doc/api + 10 AI tasks, 3 overlap) |
| Pending | 1 (AI-7) |
| Future | Many |

**Focus on completed items first. Don't worry about future items yet!**