# Experiment report
## Research question and objectives
How do bounded-buffer management policies affect information freshness and abnormal event preservation in remote patient monitoring under intermittent connectivity? The experiment compares four storage rules using the same synthetic acquisitions and simulated outages. It aims to characterize the trade-off, not claim clinical effectiveness or firmware performance.

## Hypotheses
H1: retaining the newest readings tends to reduce AoI during prolonged overflow relative to drop-newest. 
H2: event-aware retention increases abnormal episode preservation relative to FIFO rules under overflow. 
H3: improvements in preservation can carry a freshness cost. These were specified before the main run and were not used to tune P4.

## Source evidence
The firmware evidence comes from the separate [Smart IoT Patient Monitoring System repository](https://github.com/yisMeb/Smart-IoT-Patient-Monitoring-System), at [upstream commit `370d9fc4d1d2a9373213b5e3224ba37ee3701a7b`](https://github.com/yisMeb/Smart-IoT-Patient-Monitoring-System/commit/370d9fc4d1d2a9373213b5e3224ba37ee3701a7b). Exact file, lines and interpretation are in the [source mapping](../../references/source_code_mapping.md). The original code has five-second nominal reporting, a 720 reading volatile FIFO queue, drop-newest admission, a five-second reconnection attempt interval and a 100ms publish-attempt throttle. The simulation does not execute firmware or measure Wi-Fi, MQTT, ESP32 or AWS performance.

## Methodology and configurations
See [methodology.md](methodology.md) and [experiments.yaml](config/experiments.yaml). The main balanced design has 3 capacities × 6 outage durations × 3 modeled service rates × 3 episode conditions × 30 paired seeds × 4 policies = 19,440 runs. Acquisition lasts three hours, with a 2.5-hour recovery tail. No real patient observations or human participants were used.

## Policies
P1: discard disconnected readings.
P2: FIFO, reject incoming when full. 
P3: FIFO, evict oldest when full. 
P4: FIFO, evict oldest routine when possible, if all retained readings are abnormal, reject an incoming routine or evict the oldest abnormal for an incoming abnormal. P2–P4 have equal capacity and service slots.

## Metric definitions
AoI(t) = t − maximum acquisition timestamp received by t. Mean AoI is the time integral over the acquisition window divided by that window, median, p95 and peak are time-weighted ages. Initial freshness is a virtual timestamp-zero update. Delivery ratio is unique delivered/generated, overall and by abnormality. Episode preservation is episodes with ≥1 reading delivered/generated episodes. Complete, lost and within-episode fractions measure historical completeness. Episode delay is first corresponding receipt minus first generated abnormal reading, conditional on detection. Deadline rates use all episodes. Queue occupancy, losses, latency, recovery time and pending counts are recorded. An episode with a delivered measurement is not equivalent to a diagnosis.

## Test results
Nine automated tests pass. They cover policy eviction, no outage, overflow, short and repeated interruptions, reconnection, FIFO, pending conservation, deterministic generation, hand-calculated AoI, late historical receipt, episode preservation and zero-episode handling. Pilot: 192 runs, every run passed conservation and had zero pending readings after recovery. The pilot revealed that initially measuring AoI through the quiet recovery tail inflated it, the AoI window was corrected before the main run and the pilot was rerun. The final validator checked conservation in all 19,440 main and 960 supplementary runs and matched 41,990,400 compressed logged events to every main run's delivery and loss counts.

## Quantitative findings and statistical analysis
All 19,440 main runs completed in 407.8 seconds. Every generated reading was delivered, dropped or pending, maximum pending at the boundary was zero. Across the balanced design, mean AoI was 536.04 s (P1), 562.24 s (P2), 547.68 s (P3) and 548.74 s (P4). Overall delivery ratios were 0.787 for P1 and 0.887 for each buffered policy. Abnormal measurement delivery was 0.780, 0.878, 0.883 and 0.996 respectively. Mean episode preservation among runs with at least one abnormal episode was 0.782, 0.882, 0.883 and 0.996. There were 1,512 zero-episode policy runs (378 paired cells), their episode ratios are missing by design.

The P4−P3 seed-cluster paired mean difference in episode preservation was +0.1122, with 95% bootstrap CI [0.0987, 0.1281]. P4−P2 was +0.1159 [0.1058, 0.1268]. P4−P3 mean AoI difference was +1.0576 s [0.9193, 1.2020], while P4−P2 was −13.5005 s [−13.6374, −13.3636]. These are averages over the balanced scenario grid, not estimates for a real deployment. Each interval resamples 30 independent seed clusters, retaining within-seed scenario dependence. Full descriptive means, SDs, medians, IQRs, per-scenario intervals and paired effects are in `results/tables`.

At 120 minutes of outage, one reading/s and a 120-reading buffer, episode preservation was 0.355 (P2), 0.364 (P3) and 0.941 (P4). Corresponding mean AoI was 2485.38, 2411.99 and 2427.46 s. At 720 readings under the same outage and rate, preservation was 0.671 (P2), 0.639 (P3) and 1.000 (P4), while mean AoI was 2798.08, 2557.75 and 2564.31 s. At that 720-reading/120-minute setting, increasing modeled service from 1 to 10 readings/s reduced P4 mean AoI from 2564.31 to 2420.44 s, preservation remained 1.000. These are sensitivity results under the specified generator, not measured throughput.

An exploratory supplementary study ran 960 paired simulations with three repeated outages of 5 or 15 minutes. At a 120-reading buffer and three 15-minute outages, mean episode preservation was 0.948 (P2), 0.942 (P3) and 1.000 (P4), mean AoI was 130.70, 124.60 and 124.73 s. At 720 readings, all buffered policies preserved all episodes in those repeated-outage scenarios. This study was run after the frozen main analysis and did not change policy rules.

## Unexpected findings and trade-offs
P4 improved episode preservation in 1,038 paired cells versus P3 and tied in 3,444, it was never worse in this model. However, P4 had higher AoI in 1,122 cells and tied in 3,738. Among 4,323 cells where both detected an episode, P4's conditional first-episode delay was longer in 888 and tied in 3,435. Its seed-cluster paired mean delay difference versus P3 was +272.62 s [239.15, 305.39]. Thus preservation can favor older abnormal readings at the cost of prompt delivery and freshness. In the 120-minute, one/s, 120-capacity setting, mean delay among detected episodes was 2361.09 s for P4 versus 84.24 s for P3. Because undetected episodes are omitted from conditional delay, that comparison must be read alongside preservation and deadline rates, P1's very short conditional delay is especially selected toward episodes occurring while connected.

With no outage, all four policies delivered every reading and preserved every generated episode. P1 mean AoI was 2.50 s and P2–P4 mean AoI 2.93 s because buffered readings use the next service slot. This is a scheduling effect, not an outage finding. Equal eventual delivery ratios among P2–P4 reflect equal capacity and complete recovery in this finite experiment, retention changes *which* readings survive, not how many.

## Threats to validity and limitations
Synthetic physiology is a model, not patient data. The perturbation and threshold rules are not clinically validated. Episodes follow a Poisson/uniform generator and may not resemble real physiology. Outages and service are deterministic given configuration, and successful receipt is assumed whenever connected service completes. The firmware has sensor smoothing, invalid-reading gates, real loop timing and publish failures that the model omits. The modeled rates are not hardware measurements. P1's direct send is an idealized no-buffer comparator. One patient and a single outage are used in the frozen main factorial design, the supplementary repeated-outage grid is narrower. The recovery tail is finite, so pending is tracked explicitly. Compressed event logs cover all main runs, while per-measurement outcome CSVs are exported for one paired representative scenario. Across-condition pooled intervals describe this chosen scenario mixture and do not establish general clinical or network performance. Episode-level ratios are unavailable when a seed generates no abnormal episode. Conditional episode delays are vulnerable to detection selection, use them with episode loss and all-episode deadline rates.

## Potential scientific contribution
The experiment can provide reproducible evidence about when a fixed-capacity event-aware queue preserves synthetic abnormal episodes and the associated freshness cost, conditional on the stated model. Novelty relative to published work has not been established.

## Reproduction
Run the commands in [README.md](README.md) using the pinned requirements and committed configuration. CSVs contain run seeds and outputs, JSON manifests contain runtime and seed lists, and figure-source CSV plus plotting script regenerate PNG/PDF figures. All results are local.

## Remaining questions
How robust are results to physiological generators, correlated episodes, different outage processes, competing traffic, service failures, and clinically meaningful definitions of event detection? Hardware and field validation would be separate studies.
