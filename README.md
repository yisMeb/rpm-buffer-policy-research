# RPM buffer policy research

This repository contains a local simulation study of bounded patient-monitoring buffers during intermittent connectivity. It compares four policies on synthetic readings and outages. It does not run device firmware or process patient data.

The study uses firmware from the separate [Smart IoT Patient Monitoring System repository](https://github.com/yisMeb/Smart-IoT-Patient-Monitoring-System) as source evidence. The [source mapping](references/source_code_mapping.md) identifies the upstream revision and the specific firmware lines used to inform the model. That upstream commit is not a commit in this repository.

## Repository guide

- `src/`: data generation, network model, buffer policies, simulator, and metrics.
- `config/`: Version 1 and Version 2 experiment settings.
- `experiments/`: Version 2 run, analysis, export, figure, and validation scripts.
- `tests/`: Version 2 tests.
- `versions/v1/`: preserved Version 1 code, documentation, and results.
- `versions/v2/results/`: Version 2 data, figures, methodology, and report.
- `results/`: original Version 1 result artifacts retained for comparison.

Start with the [Version 2 methodology](versions/v2/results/methodology.md) and [experiment report](versions/v2/results/EXPERIMENT_REPORT.md). For reproduction commands, see the [Version 2 README](versions/v2/results/README.md). The [Version 1 README](versions/v1/README.md) documents the archived study.
