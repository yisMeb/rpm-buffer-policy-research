# research experiment
This directory preserves Version 1 of a simulation study of bounded patient-monitoring buffers under intermittent connectivity. The study uses firmware from the separate [Smart IoT Patient Monitoring System repository](https://github.com/yisMeb/Smart-IoT-Patient-Monitoring-System) as source evidence; see the [upstream source mapping](../../references/source_code_mapping.md).

## Reproduce

Use Python 3.12.4. From repository root:

```powershell
python -m pip install -r versions/v1/requirements.txt
python -m pytest versions/v1/tests -q
python versions/v1/experiments/run_pilot.py
python versions/v1/experiments/run_experiments.py
python versions/v1/experiments/run_repeated.py
python versions/v1/experiments/analyze_results.py
python versions/v1/experiments/export_all_event_logs.py
python versions/v1/experiments/export_event_logs.py
python versions/v1/experiments/generate_figures.py
python versions/v1/experiments/validate_results.py
```

The commands generate pilot/main run data, an exploratory repeated-outage dataset, tables and figures. Figure PDFs are created with Pillow. `results/raw` holds run-level metrics, a compressed event log for every main run, paired representative event and per-measurement outcome logs, an occupancy trace, and manifests with seed lists and runtime. `results/processed` holds figure source data. `results/tables` holds configuration, scenario, overall, statistics, paired effects and sensitivity CSVs. `results/figures` holds PNG/PDF pairs. Run-level conservation is checked for every run.

Configuration: [experiments.yaml](config/experiments.yaml). Methods and assumptions: [methodology.md](methodology.md). Firmware mapping: [upstream source mapping](../../references/source_code_mapping.md). Results and limits: [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md).
