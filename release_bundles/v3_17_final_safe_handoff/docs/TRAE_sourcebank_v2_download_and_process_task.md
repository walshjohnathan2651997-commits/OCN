# TRAE TASK: Download and process Source Bank v2 candidates

Goal: download this whole candidate source batch into a traceable PDF/HTML material bank, then build source-bank and evidence-entry audit files.

Do NOT create gold labels. Do NOT set human_audited=true. Do NOT create train/dev/test splits. Do NOT train models. Do NOT call LLM APIs. Do NOT edit the paper/docx. Do NOT delete original files.

## Input files

- Raw 128 candidate rows: `D:\ocn\data\source_bank\source_bank_v2_raw_128_candidates.csv`
- Unique URL 94 candidates: `D:\ocn\data\source_bank\source_bank_v2_unique_url_94_candidates.csv`
- Recommended download list: `D:\ocn\data\source_bank\source_bank_v2_download_recommended_93.csv`

Recommended behavior: download the 93-row recommended list first. The 94th unique URL is Waymax / arXiv 2310.08710, which is already a known seed50 duplicate. If full mirror is requested, download all 94 but mark the duplicate.

## Output directories

```text
D:/ocn/data/source_bank_v2/
D:/ocn/data/source_bank_v2/pdfs/
D:/ocn/data/source_bank_v2/html/
D:/ocn/data/source_bank_v2/metadata/
D:/ocn/data/source_bank_v2/audit/
D:/ocn/data/source_bank_v2/evidence_candidates/
D:/ocn/reports/source_bank_v2/
```

## Required output files

```text
D:/ocn/data/source_bank_v2/source_bank_v2_unique_sources.csv
D:/ocn/data/source_bank_v2/evidence_entry_bank_v2.csv
D:/ocn/data/source_bank_v2/audit/download_manifest.csv
D:/ocn/data/source_bank_v2/audit/source_dedup_audit.csv
D:/ocn/data/source_bank_v2/audit/source_quality_score.csv
D:/ocn/data/source_bank_v2/audit/failed_downloads.csv
D:/ocn/data/source_bank_v2/evidence_candidates/evidence_candidate_spans.csv
D:/ocn/reports/source_bank_v2/source_bank_v2_download_report.md
```

## Processing steps

1. Read `source_bank_v2_unique_url_94_candidates.csv`.
2. Build blacklist from current 76/64 candidate pool, seed50 URLs/arXiv IDs, and locally downloaded PDFs.
3. Deduplicate by arxiv_id exact match, normalized title exact match, and fuzzy title match >= 0.92.
4. Download PDFs. For arXiv, use `https://arxiv.org/pdf/{arxiv_id}`. If PDF download fails, save the abs/html page.
5. Save files as `{source_id}__{arxiv_id_or_hash}.pdf` or `.html`.
6. Extract metadata: source_id, domain, title, url, arxiv_id, pdf_path, html_path, download_status, duplicate flags, title_verified.
7. Score evidence density:
   - 5 = clear setup + metrics + results + limitations; excellent evidence source.
   - 4 = benchmark/system/evaluation paper; good evidence source.
   - 3 = usable but needs manual span selection.
   - 2 = mostly review/background; defer.
   - 1 = not suitable.
8. For score >= 4 sources, extract 1-3 evidence candidate spans. Do NOT generate claims yet.
9. Evidence span types: experiment_setup, metric_result, limitation, deployment_boundary, comparison, applicability_scope.
10. Keep page/section/source_location and evidence_text_sha256 for every span.

## CSV schemas

### source_bank_v2_unique_sources.csv

```text
source_id,domain,title,url,arxiv_id,is_seed50_duplicate,is_downloaded_duplicate,is_current_pool_duplicate,is_internal_duplicate,download_status,pdf_path,html_path,title_verified,evidence_density_score,status,notes
```

### evidence_entry_bank_v2.csv

```text
entry_id,source_id,evidence_type,recommended_claim_dimension,extraction_priority,source_location,evidence_text_preview,evidence_text_sha256,notes
```

### evidence_candidate_spans.csv

```text
span_id,source_id,domain,title,source_location,evidence_type,evidence_text,evidence_text_sha256,extraction_quality,claim_generation_ready,notes
```

## First-round admission rule

Only sources matching all of the following should enter first evidence extraction:

```text
evidence_density_score >= 4
is_seed50_duplicate = false
is_current_pool_duplicate = false
download_status = success
```

## Candidate links, unique URL list

| source_id | domain | title | url | arxiv_id |
|---|---|---|---|---|
| AD-001 | autonomous_driving | nuPlan-R: A Closed-Loop Planning Benchmark for Autonomous Driving via Reactive Multi-Agent Simulation | https://arxiv.org/abs/2511.10403 | 2511.10403 |
| AD-002 | autonomous_driving | Open-Source Modular Benchmark for Diffusion-Based Motion Planning in Closed-Loop Autonomous Driving | https://arxiv.org/abs/2603.01023 | 2603.01023 |
| AD-003 | autonomous_driving | HiDrive: A Closed-Loop Benchmark for High-Level Autonomous Driving | https://arxiv.org/abs/2605.09972 | 2605.09972 |
| AD-004 | autonomous_driving | Bench2Drive-Robust: Benchmarking Closed-Loop Autonomous Driving under Deployment Perturbations | https://arxiv.org/abs/2605.18059 | 2605.18059 |
| AD-005 | autonomous_driving | Bench2Drive-R: Realistic Reactive Closed-Loop Benchmark | https://arxiv.org/abs/2412.09647 | 2412.09647 |
| AD-006 | autonomous_driving | Bench2ADVLM | https://arxiv.org/abs/2508.02028 | 2508.02028 |
| AD-007 | autonomous_driving | RoboDriveVLM / RoboDriveBench | https://arxiv.org/abs/2512.01300 | 2512.01300 |
| AD-008 | autonomous_driving | DriveBench: Are VLMs Ready for Autonomous Driving? | https://arxiv.org/abs/2501.04003 | 2501.04003 |
| AD-009 | autonomous_driving | ScenePilot-Bench | https://arxiv.org/abs/2601.19582 | 2601.19582 |
| AD-010 | autonomous_driving | DSBench: Driving Safety Benchmark | https://arxiv.org/abs/2511.14592 | 2511.14592 |
| AD-011 | autonomous_driving | DriveVLM | https://arxiv.org/abs/2402.12289 | 2402.12289 |
| AD-012 | autonomous_driving | Bench2Drive | https://arxiv.org/abs/2406.03877 | 2406.03877 |
| AD-013 | autonomous_driving | Waymax [seed50_duplicate] | https://arxiv.org/abs/2310.08710 | 2310.08710 |
| AD-014 | autonomous_driving | NAVSIM | https://arxiv.org/abs/2406.15349 | 2406.15349 |
| AD-015 | autonomous_driving | DriveE2E: Closed-Loop Benchmark for End-to-End Autonomous Driving through Real-to-Simulation | https://arxiv.org/abs/2509.23922 | 2509.23922 |
| AD-016 | autonomous_driving | HABIT | https://arxiv.org/abs/2511.19109 | 2511.19109 |
| AD-017 | autonomous_driving | V-Max: Making RL Practical for Autonomous Driving | https://arxiv.org/abs/2503.08388 | 2503.08388 |
| AD-018 | autonomous_driving | URB: Urban Routing Benchmark for RL-equipped Connected Autonomous Vehicles | https://arxiv.org/abs/2505.17734 | 2505.17734 |
| AD-019 | autonomous_driving | Optimizing Efficiency of Mixed Traffic through Reinforcement Learning | https://arxiv.org/abs/2501.16728 | 2501.16728 |
| AD-020 | autonomous_driving | Real-World Deployment of MARL-Based Variable Speed Limit Control | https://arxiv.org/abs/2503.01017 | 2503.01017 |
| AD-021 | autonomous_driving | CoLLMLight: Cooperative LLM Agents for Network-Wide Traffic Signal Control | https://arxiv.org/abs/2503.11739 | 2503.11739 |
| AD-022 | autonomous_driving | Virtual Roads | Smarter Safety: Digital Twin Framework for Mixed Autonomous Traffic |  |
| AD-023 | autonomous_driving | Historical Prediction Attention for Work Zone Safety in a Digital Twin Environment | https://arxiv.org/abs/2508.06544 | 2508.06544 |
| AD-024 | autonomous_driving | Lessons Learned from Real-World Multi-Sensor Fusion for Work Zone Safety | https://arxiv.org/abs/2508.01599 | 2508.01599 |
| MARL-001 | marl | Multi-Agent Craftax | https://arxiv.org/abs/2511.04904 | 2511.04904 |
| MARL-002 | marl | Alem: Open-Ended Multi-Agent Coordination in Language Agents | https://arxiv.org/abs/2606.08340 | 2606.08340 |
| MARL-003 | marl | CAMAR: Continuous Actions Multi-Agent Routing | https://arxiv.org/abs/2508.12845 | 2508.12845 |
| MARL-004 | marl | Sequential Industrial Control MARL Benchmark | https://arxiv.org/abs/2510.20408 | 2510.20408 |
| MARL-005 | marl | MEAL: Continual Multi-Agent Reinforcement Learning Benchmark | https://arxiv.org/abs/2506.14990 | 2506.14990 |
| MARL-006 | marl | Tool-RoCo Multi-Robot Cooperation Benchmark | https://arxiv.org/abs/2511.21510 | 2511.21510 |
| MARL-007 | marl | MPAC Multi-Principal Agent Coordination Protocol | https://arxiv.org/abs/2604.09744 | 2604.09744 |
| MARL-008 | marl | Historical Interaction-Enhanced Shapley Policy Gradient | https://arxiv.org/abs/2511.07778 | 2511.07778 |
| MARL-009 | marl | QLLM Credit Assignment for MARL | https://arxiv.org/abs/2504.12961 | 2504.12961 |
| MARL-010 | marl | Extended Benchmarking of MARL Algorithms in Complex Fully Cooperative Tasks | https://arxiv.org/abs/2502.04773 | 2502.04773 |
| MARL-011 | marl | WFCRL: Multi-Agent Reinforcement Learning Benchmark for Wind Farm Control | https://arxiv.org/abs/2501.13592 | 2501.13592 |
| MARL-012 | marl | Coopetition-Gym v1 | https://arxiv.org/abs/2605.02063 | 2605.02063 |
| MARL-013 | marl | Agent-Attention Multi-Agent Multi-Objective Reinforcement Learning | https://arxiv.org/abs/2511.08926 | 2511.08926 |
| MARL-014 | robotics | NavBench: Unified Robotics Benchmark for RL-Based Autonomous Navigation | https://arxiv.org/abs/2505.14526 | 2505.14526 |
| MARL-015 | robotics | Sim-to-Real Transfer for Mobile Robots with RL | https://arxiv.org/abs/2501.02902 | 2501.02902 |
| MARL-016 | robotics | Can Context Bridge the Reality Gap? | https://arxiv.org/abs/2511.04249 | 2511.04249 |
| MARL-017 | robotics | RealAIGym AI Olympics RL Benchmark | https://arxiv.org/abs/2503.15290 | 2503.15290 |
| MARL-018 | robotics | GRaD-Nav++ Drone Navigation with Gaussian Radiance Fields | https://arxiv.org/abs/2506.14009 | 2506.14009 |
| MARL-019 | robotics | LLM-Agents Driven Automated Simulation Testing of sUAS | https://arxiv.org/abs/2501.11864 | 2501.11864 |
| CYB-001 | cyber_defense | AgentCyberRange | https://arxiv.org/abs/2606.14295 | 2606.14295 |
| CYB-002 | cyber_defense | CAIBench: Cybersecurity AI Benchmark | https://arxiv.org/abs/2510.24317 | 2510.24317 |
| CYB-003 | cyber_defense | Dynamic Cyber Ranges | https://arxiv.org/abs/2604.24184 | 2604.24184 |
| CYB-004 | cyber_defense | Explainable Autonomous Cyber Defense with Adversarial MARL | https://arxiv.org/abs/2604.04442 | 2604.04442 |
| CYB-005 | cyber_defense | Q-BIRD: Belief-Space RL for Autonomous Cyber Defense in IoV | https://arxiv.org/abs/2606.07796 | 2606.07796 |
| CYB-006 | cyber_defense | DeepXplain: XAI-Guided Autonomous Defense Against APT Campaigns | https://arxiv.org/abs/2603.21296 | 2603.21296 |
| CYB-007 | cyber_defense | LLM-Based Reward Design for Autonomous Cyber Defense | https://arxiv.org/abs/2511.16483 | 2511.16483 |
| CYB-008 | cyber_defense | Large Language Models are Autonomous Cyber Defenders | https://arxiv.org/abs/2505.04843 | 2505.04843 |
| CYB-009 | cyber_defense | Hierarchical Multi-Agent Reinforcement Learning for Cyber Network Defense | https://arxiv.org/abs/2410.17351 | 2410.17351 |
| CYB-010 | cyber_defense | Quantitative Resilience Modeling for Autonomous Cyber Defense | https://arxiv.org/abs/2503.02780 | 2503.02780 |
| CYB-011 | cyber_defense | Entity-based Reinforcement Learning for Autonomous Cyber Defence | https://arxiv.org/abs/2410.17647 | 2410.17647 |
| CYB-012 | cyber_defense | Towards Production-Worthy Simulation for Autonomous Cyber Operations | https://arxiv.org/abs/2508.19278 | 2508.19278 |
| POL-001 | policy_simulation | PolicySimEval | https://arxiv.org/abs/2502.07853 | 2502.07853 |
| POL-002 | policy_simulation | LLM Agent Simulations for Emergency Preparedness | https://arxiv.org/abs/2509.21868 | 2509.21868 |
| POL-003 | policy_simulation | Are LLM Agents Behaviorally Coherent? | https://arxiv.org/abs/2509.03736 | 2509.03736 |
| POL-004 | policy_simulation | SocioVerse | https://arxiv.org/abs/2504.10157 | 2504.10157 |
| POL-005 | policy_simulation | Impact of Heatwaves on Population Health: LLM-Enhanced ABM | https://arxiv.org/abs/2605.15918 | 2605.15918 |
| POL-006 | policy_simulation | Too Human to Model: Uncanny Valley of LLMs in Social Simulation | https://arxiv.org/abs/2507.06310 | 2507.06310 |
| POL-007 | policy_simulation | SimCity: Multi-Agent Urban Development Simulation | https://arxiv.org/abs/2510.01297 | 2510.01297 |
| POL-008 | policy_simulation | Emergence of Altruism in LLM Agents Society | https://arxiv.org/abs/2509.22537 | 2509.22537 |
| POL-009 | policy_simulation | Domain-driven Metrics for RL in Epidemic Control using ABM | https://arxiv.org/abs/2508.05154 | 2508.05154 |
| POL-010 | policy_simulation | Barriers to Healthcare: ABM to Mitigate Inequity | https://arxiv.org/abs/2507.23644 | 2507.23644 |
| POL-011 | policy_simulation | Agent-based Modeling meets Capability Approach for Homelessness Policy | https://arxiv.org/abs/2503.18389 | 2503.18389 |
| POL-012 | policy_simulation | TaxAgent: How Large Language Model Designs Fiscal Policy | https://arxiv.org/abs/2506.02838 | 2506.02838 |
| POL-013 | policy_simulation | LLM Economist | https://arxiv.org/abs/2507.15815 | 2507.15815 |
| POL-014 | policy_simulation | LLMs for Large-Scale Urban Complex Mobility Simulation | https://arxiv.org/abs/2505.21880 | 2505.21880 |
| POL-015 | policy_simulation | GenWorld Urban Simulation Infrastructure | https://arxiv.org/abs/2606.27650 | 2606.27650 |
| POL-016 | policy_simulation | LLM-Powered Social Digital Twins | https://arxiv.org/abs/2601.06111 | 2601.06111 |
| POL-017 | policy_simulation | MobiVerse Urban Mobility Simulation | https://arxiv.org/abs/2506.21784 | 2506.21784 |
| POL-018 | policy_simulation | Epi-LLM Framework | https://arxiv.org/abs/2606.02867 | 2606.02867 |
| POL-019 | policy_simulation | VacSim: Generative Agents for Vaccine Hesitancy Policy Simulation | https://arxiv.org/abs/2503.09639 | 2503.09639 |
| POL-020 | policy_simulation | Tradable Credit Schemes via Agent-Based Simulation | https://arxiv.org/abs/2502.11822 | 2502.11822 |
| POL-021 | policy_simulation | PolicySim Social Simulation Sandbox | https://arxiv.org/abs/2603.19649 | 2603.19649 |
| DT-001 | digital_twin | TwinLoop: Simulation-in-the-Loop Digital Twins for Online MARL | https://arxiv.org/abs/2604.06610 | 2604.06610 |
| DT-002 | digital_twin | Digital Twin Calibration with Model-Based Reinforcement Learning | https://arxiv.org/abs/2501.02205 | 2501.02205 |
| DT-003 | digital_twin | Digital Twin-Enabled Real-Time Control in Robotic Additive Manufacturing | https://arxiv.org/abs/2501.18016 | 2501.18016 |
| DT-004 | digital_twin | Digital Twin RL with Human Assistive Teleoperation | https://arxiv.org/abs/2406.00732 | 2406.00732 |
| DT-005 | digital_twin | LSDTs: LLM-Augmented Semantic Digital Twins | https://arxiv.org/abs/2508.06799 | 2508.06799 |
| DT-006 | digital_twin | CDA-SimBoost | https://arxiv.org/abs/2507.19707 | 2507.19707 |
| DT-007 | digital_twin | Digital Twin-Driven Pavement Health Monitoring | https://arxiv.org/abs/2511.02957 | 2511.02957 |
| DT-009 | digital_twin | Digital Twin Framework for Generation-IV Reactors | https://arxiv.org/abs/2506.17258 | 2506.17258 |
| DT-010 | digital_twin | RL-Enhanced Clinical Decision Support via Digital Twin | https://arxiv.org/abs/2508.17212 | 2508.17212 |
| DT-011 | digital_twin | Introduction to Digital Twins for the Smart Grid | https://arxiv.org/abs/2602.14256 | 2602.14256 |
| DT-012 | digital_twin | RL for Optimal Control in Microgrids with Digital Twin | https://arxiv.org/abs/2506.22995 | 2506.22995 |
| DT-013 | digital_twin | Digital Twin-Empowered DRL for VNF Migration | https://arxiv.org/abs/2508.20957 | 2508.20957 |
| DT-014 | digital_twin | Digital Twin-Guided Energy Management in 6G Smart Cities | https://arxiv.org/abs/2508.18516 | 2508.18516 |
| DT-015 | digital_twin | Mixed Autonomous Traffic Safety Digital Twin | https://arxiv.org/abs/2504.17968 | 2504.17968 |
| DT-016 | digital_twin | APDT: Access Point Digital Twin | https://arxiv.org/abs/2511.23009 | 2511.23009 |
| DT-017 | digital_twin | Traffic Safety Analysis with Digital Twin Technology | https://arxiv.org/abs/2502.09561 | 2502.09561 |
| DT-018 | digital_twin | FOGNITE: Federated Learning-Enhanced Fog-Cloud Architecture with Digital Twin Validation | https://arxiv.org/abs/2507.16668 | 2507.16668 |
| DT-019 | digital_twin | PINN-DT: Smart Building Energy Optimization with Digital Twin | https://arxiv.org/abs/2503.00331 | 2503.00331 |

## Final response required from TRAE

Report only:

1. Number of successful PDF downloads.
2. Failed download list.
3. Source-level unique count.
4. seed50/current-pool duplicate count.
5. Number of sources with evidence_density_score >= 4.
6. Number of evidence candidate spans extracted.
7. Paths to the required output files.
8. Whether the batch is ready for next-step claim generation.