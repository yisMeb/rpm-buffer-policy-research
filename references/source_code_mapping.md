# Firmware evidence

Upstream source: [Smart IoT Patient Monitoring System](https://github.com/yisMeb/Smart-IoT-Patient-Monitoring-System), a separate repository from this simulation study.
Upstream revision inspected: [`370d9fc4d1d2a9373213b5e3224ba37ee3701a7b`](https://github.com/yisMeb/Smart-IoT-Patient-Monitoring-System/commit/370d9fc4d1d2a9373213b5e3224ba37ee3701a7b).
Firmware file in that repository: `frontend/Device/ESP32 Board/sketch_jan24a/sketch_jan24a.ino`.

| Property | Source lines | Evidence |
|---|---:|---|
| Nominal reporting period 5 s | 12, 218, 248 | `REPORTING_PERIOD_MS=5000`; actual condition is `>` and needs five valid sensor readings. |
| Reconnection attempt interval 5 s | 13, 94–112 | `maintainConnections`, contingent on loop execution and Wi-Fi state. |
| Publish attempt interval 100 ms | 14, 138–153 | `flushPendingReadings`; rate is an attempt throttle, not measured throughput. |
| Queue capacity 720 | 15, 35–38 | Fixed `HealthReading` array and indices in RAM. |
| Drop newest on full | 126–135 | `enqueueReading` returns false without changing queue. |
| FIFO transmission | 138–153 | Publishes `pendingReadings[pendingHead]`; advances head only on successful publish. |
| Volatile storage | 35–40 | Global RAM array; no persistence shown in firmware. |

This is source inspection, not execution or hardware validation. The research model assumes exact five-second generation, successful connected transmission, a configurable service rate, deterministic reconnection delay and synthetic abnormality labels. Firmware publishes only values, so measurement IDs, timestamps and episodes are research instrumentation, not fields in the original payload.
