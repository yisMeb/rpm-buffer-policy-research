# Local research experiment

This directory contains Version 2 results and documentation for a simulation study of bounded patient-monitoring buffers under intermittent connectivity. The study uses firmware from the separate [Smart IoT Patient Monitoring System repository](https://github.com/yisMeb/Smart-IoT-Patient-Monitoring-System) as source evidence; see the [upstream source mapping](../../../references/source_code_mapping.md). It does not run the ESP32 firmware or process real patient data.

## Reproduce

Use Python 3.12.4. From repository root:

```powershell
python -m pip install -r requirements.txt
python -m pytest tests -q
python experiments/run_pilot.py
python experiments/run_experiments.py
python experiments/run_repeated.py
python experiments/run_episode_sensitivity.py
python experiments/analyze_results.py
python experiments/compare_versions.py
python experiments/export_all_event_logs.py
python experiments/export_event_logs.py
python experiments/export_ground_truth.py
python experiments/generate_figures.py
python experiments/validate_results.py
```

The commands generate Version 2 pilot/main runs, repeated-outage and episode-generator sensitivity datasets, tables and figures. Version 1 results, report, code and configuration are preserved in `versions/v1`, the original `results/` also remains unchanged. Version 2 data are in `versions/v2/results/`, including a compressed event log for every main run, episode ground truth, paired representative outcomes, run metrics, tables and PNG/PDF figures. The all-event export is large and can be skipped when only run-level results are needed, the main simulation already verifies conservation for every run.

Version 2 configuration: [experiments_v2.yaml](../../../config/experiments_v2.yaml). Methods and correction log: [methodology.md](methodology.md) and [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md). Firmware mapping: [upstream source mapping](../../../references/source_code_mapping.md).
