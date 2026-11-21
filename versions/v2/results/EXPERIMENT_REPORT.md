
## Research question, objective and hypotheses

How do bounded-buffer policies affect information freshness and preservation of abnormal physiological episodes under intermittent connectivity? This source-informed simulation compares P1 no offline buffer, P2 FIFO/drop-newest, P3 FIFO/drop-oldest and P4 event-aware retention on paired synthetic sequences. The pre-specified expectations were that fresher retention lowers AoI, P4 preserves more ground-truth episodes during overflow, and preservation can delay delivery. These are modeling hypotheses, not claims of clinical benefit or scientific novelty.

## Version 1 preservation and audit corrections
The complete Version 1 code, configuration, report and results are archived at `versions/v1/`, its main run CSV hash is in `versions/v1/ARCHIVE_MANIFEST.md`. The original `results/` directory is unchanged. Version 2 writes to `versions/v2/results/`. P4's capacity, decision rule and service rate were **not tuned** after inspecting Version 1.

| Audit issue | Version 1 | Version 2 correction |
|---|---|---|
| Queue occupancy | Recorded only with detailed event logging. most run rows incorrectly showed zero. | Recorded after every acquisition in every run, independent of logging. |
| P1 scheduling | Connected readings sent immediately, bypassing the common slot clock. | P1 uses the same service slots as P2–P4 and cannot retain through disconnection. |
| Overlapping episodes | Only the first active episode was assigned to a reading. an episode could disappear from the denominator. Threshold crossing was required for assignment. | Every generated episode remains in ground truth, readings list all active episode IDs, and threshold labels are separate. |
| Loss accounting | All dropped readings were labeled overflow, even P1 disconnection losses. | Network disconnection, overflow, no-buffer contention and pending are distinct, with conservation checks. |
| Recovery time | Boundary behavior lacked hand-calculated tests. | Tests cover empty at reconnection, clearing exactly then, clearing later and unfinished backlog. |
| Episode deadlines | Calculated but subordinate to eventual preservation in reporting. | 60-, 300- and 900-second delivery rates are co-primary outcomes. |
| Generator assumptions | Only Poisson counts/uniform starts were examined. | Fixed-count uniform and clustered longer episodes are explicit sensitivity models. |

## Source evidence and scope

The firmware evidence comes from the separate [Smart IoT Patient Monitoring System repository](https://github.com/yisMeb/Smart-IoT-Patient-Monitoring-System), at [upstream commit `370d9fc4d1d2a9373213b5e3224ba37ee3701a7b`](https://github.com/yisMeb/Smart-IoT-Patient-Monitoring-System/commit/370d9fc4d1d2a9373213b5e3224ba37ee3701a7b). Exact paths and lines are in the [source mapping](../../../references/source_code_mapping.md). The code supports nominal five-second reporting, a 720-reading volatile FIFO queue, drop-newest admission, five-second reconnect attempts and a 100-ms publish-attempt throttle. The simulation does not execute the firmware or measure ESP32, MQTT, AWS or real network throughput.

## Configuration, policies and methodology

The frozen Version 2 main grid has 3 capacities (120, 360, 720) × 6 outage durations (0, 5, 15, 30, 60, 120 minutes) × 3 modeled rates (1, 5, 10 readings/s) × 3 episode conditions × 30 paired seeds × 4 policies = **19,440 runs**. Acquisition lasts three hours, followed by a 2.5-hour recovery tail. One outage begins at 30 minutes and connectivity returns five seconds after its end. Successful receipt is assumed at every connected service completion. An exploratory repeated-outage grid adds 960 runs. Two alternative episode models add 1,920 sensitivity runs. A 192-run pilot preceded the main run.

At a shared service time, transmission precedes acquisition. P1 has one transient send position while connected but no offline retention. P2 rejects an arrival when full. P3 replaces the oldest. P4 replaces the oldest threshold-routine reading when possible, with all abnormal readings retained, it rejects a routine arrival and replaces the oldest abnormal with an abnormal arrival. Retained readings transmit chronologically. P2–P4 have identical capacity and service clocks. Details are in [methodology.md](methodology.md) and the frozen [Version 2 configuration](config/experiments_v2.yaml).

## Mathematical outcomes

AoI(t) = t − max{acquisition time of readings received by t}. A delayed historical reading cannot make freshness worse by replacing a newer timestamp. A virtual timestamp-zero update defines initial age. Mean AoI integrates age over the acquisition window, median, p95 and peak are time-weighted. Unique delivered/generated defines overall and threshold-stratified reading delivery ratios.

Ground-truth episode preservation = episodes with at least one associated reading delivered / all generated episodes. The 60-, 300- and 900-second rates use first associated delivery minus true episode onset, also divided by **all** generated episodes. Episodes with no sampled reading count as lost. Complete preservation, entirely lost fraction and mean within-episode fraction measure historical completeness. Conditional first-delivery delay is reported separately, it excludes undelivered episodes and can be misleading alone. Threshold-abnormal measurement delivery is separate from ground-truth episode preservation. A delivered reading is not a clinical diagnosis.

Queue occupancy is the post-acquisition sample in each run, its mean is the mean of those samples. Network-disconnection, overflow rejection/eviction and no-buffer contention losses are disjoint. Pending is separate. Total loss at the simulation boundary is dropped plus pending. Backlog recovery is time from final reconnection to first empty queue, it is zero if already empty and missing if still backlogged at the boundary.

## Tests and validation

**17 automated tests passed, 0 failed.** New tests cover occupancy with logging on/off, equal P1/buffered service slots, pre-slot P1 disconnection, overlapping and threshold-missed ground-truth episodes, all-episode deadline denominators, distinct loss categories, pending conservation, alternative-generator reproducibility and four hand-calculated recovery boundaries. The Version 2 pilot passed conservation and paired-input checks. The main run completed in 660.6 seconds. The main, repeated-outage and episode-sensitivity datasets contain no pending readings at their recovery boundaries, all runs satisfy generated = delivered + dropped + pending. The final validator matched **41,990,400 compressed events** to delivery and separately classified loss counts in every main run, confirmed ground-truth episode counts, and checked conservation in all 960 repeated-outage and 1,920 episode-sensitivity runs.

## Quantitative Version 2 findings

Across the balanced main design, run-level means are:

| Policy | Mean AoI (s) | Reading delivery | Eventual episode preservation | Within 60 s | Within 300 s | Within 900 s |
|---|---:|---:|---:|---:|---:|---:|
| P1 | 536.48 | 0.787 | 0.783 | 0.778 | 0.783 | 0.783 |
| P2 | 562.24 | 0.887 | 0.882 | 0.769 | 0.785 | 0.807 |
| P3 | 547.68 | 0.887 | 0.883 | 0.769 | 0.790 | 0.829 |
| P4 | 548.74 | 0.887 | 0.997 | 0.769 | 0.790 | 0.834 |

There are 1,512 zero-episode policy runs (378 paired cells), episode ratios are missing for them, never treated as success. The 90 unique seed/condition input sequences contain **468 generated ground-truth episodes**. Version 1's threshold-dependent first-active-episode accounting counted only **460**. There were 679 overlap-associated reading instances involving 85 distinct ground-truth episode IDs, eight episodes were entirely absent from Version 1's evaluation denominator.

At the severe 120-minute outage, one reading/s and 120-reading capacity, eventual preservation was 0.356 (P2), 0.364 (P3) and 0.942 (P4). Yet all three delivered only 0.293 of episodes within 60 seconds, their 300-second rates were 0.301, 0.322 and 0.322, and their 900-second rates were 0.301, 0.364 and 0.379. P4 mean AoI was 2427.47 s versus 2411.99 s for P3. This is the strongest observed completeness-versus-timeliness trade-off.

Mean network-disconnection losses were 460.83 readings/run for P1 and zero for buffered policies. Mean overflow losses were zero for P1 and 243.83 for each buffered policy. No-buffer contention and pending were zero in the main grid. P1's no-outage AoI is now 2.93 s, identical to P2–P4, Version 1 gave P1 an immediate-send advantage of 0.43 s in that baseline.

## Statistical analysis and negative findings

Simulation seeds, not readings, are the stochastic units. Paired effects average matched scenario differences within each seed and resample 30 seed clusters 2,000 times for 95% bootstrap intervals. Full per-scenario means, SDs, medians, IQRs and intervals are in `versions/v2/results/tables/`.

P4−P3 eventual preservation averaged **+0.1119** [0.0974, 0.1279], but 60-second and 300-second differences were **exactly 0.0000** across all 4,482 nonempty paired cells. The 900-second difference was +0.0050 [0.0029, 0.0075]. P4−P3 AoI was +1.0578 s [0.9254, 1.1921], and conditional first-delivery delay was +272.03 s [241.47, 302.97]. P4−P1 60-second delivery was **−0.0087** [−0.0115, −0.0061]. Thus P4's large eventual gain does not establish prompt event delivery and performs worse on this early deadline comparison with P1. Conditional delay is detection-selected, so the all-episode deadline rates are the stronger timeliness evidence.

P4 never had lower eventual preservation than P3 in a paired nonempty cell (1,038 gains, 3,444 ties), but had higher AoI in 1,122 cells (3,738 ties). P4 and P3 tied in all 4,482 paired 60-second and 300-second episode rates. Equal eventual reading-delivery totals for P2–P4 arise from equal capacity and complete recovery, they retain different *which* readings.

## Version 1 versus Version 2

Matched runs have the same capacity, outage, rate, condition, seed and policy. P1 mean AoI rose from 536.04 to 536.48 s (+0.4331 s) when its instant-send advantage was removed, P2/P3 AoI did not change, and P4 changed by +0.0003 s. P2 mean occupancy peak changed from a spurious 0 to 217.17 readings, P3 did likewise, while P4 changed from 0.15 to 217.17 because only one Version 1 run logged occupancy. P1's 460.83 mean losses/run are now correctly classified as network disconnection rather than overflow. Buffered policies average 243.83 overflow losses/run. Episode counts increased from 5.1111 to 5.2000 per run as the eight omitted episodes were restored. P4 eventual preservation remained about 0.997, its P4−P3 paired preservation advantage changed from +0.1122 to +0.1119. The 60-second advantage remained zero. The principal conclusion survives as a statement about *eventual historical completeness*, while Version 2 makes the lack of early delivery benefit explicit. See `v1_v2_paired_comparison.csv` and `policy_tradeoff_by_version.csv` for all quantified changes and intervals. Versions differ in episode denominator and onset definition, so direct percentage comparisons are methodological, not new clinical observations.

## Sensitivity to episode assumptions and repeated outages

On the matched medium-condition subset (capacities 120/720, outages 15/120 minutes, rates 1/5 readings/s), baseline Poisson/uniform eventual preservation for P4 was 0.998 and 60-second delivery 0.613. Fixed-count/uniform yielded 0.992 and 0.593, clustered longer episodes yielded 0.983 and 0.541. P3 eventual preservation was 0.762, 0.756 and 0.704 respectively. P4's eventual advantage persisted, but **none** of these models produced a 60-second advantage over P3. The clustered model concentrates starts toward the middle of observation and doubles durations, so these are sensitivity probes rather than estimates of real episode frequencies. The repeated-outage study (three 15-minute outages, 120-reading capacity) yielded eventual preservation of 0.949 (P2), 0.946 (P3), 1.000 (P4), but 60-second delivery of 0.756 for all buffered policies.

## Threats to validity, contribution and unresolved questions

Physiological traces, abnormality thresholds, outage timing and modeled service rates are assumptions, not patient, hardware, MQTT or AWS measurements. A single synthetic patient, deterministic service, successful connected delivery and finite recovery tail limit generalization. The generator's overlap perturbations, fixed-count and clustered alternatives are deliberately simple. Conditional delay remains selected on detection. P1's one transient send position implements fair service scheduling but is an idealized no-offline-buffer policy. The findings may contribute reproducible evidence about a completeness/timeliness trade-off in this model, novelty and clinical relevance have not been established. Future work should test richer physiology, correlated outages, service failures, multiple patients and hardware traces without assuming the present effect sizes transfer.

## Reproduction

Use Python 3.12.4 and [pinned requirements](requirements.txt). Exact commands are in [README.md](README.md). `versions/v2/results/raw/` contains run metrics, manifests, episode ground truth and compressed events, `tables/` contains configuration, scenario, statistical, sensitivity and Version 1/2 comparison CSVs, `figures/` contains 13 figures in PNG and PDF, `processed/` contains figure source data. All work executes locally. The Version 1 archive is never overwritten.
