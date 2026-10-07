# SRE Incident Response & Triage Runbook

## Telemetry Observability & Signal Pipeline

**Classification:** Internal SRE On-Call Documentation  
**Service Tier:** Tier 1 (Mission Critical Instrumentation)  
**Primary On-Call:** Systems & Observability SRE Rotation  
**Escalation Path:** Accelerator Operations Specialist / Hardware On-Call  

---

## 🚨 Alert Triage Procedures

### 1. Alert: `TelemetryCriticalBurnRate1h`
- **Severity**: Critical (P1 - Page)
- **Condition**: Error budget burning at $\ge 14.4\times$ the sustainable monthly consumption rate over 1 hour.
- **Impact**: Rapid depletion of availability error budget; beam telemetry failure imminent.

#### Diagnostics & Triage:
1. Inspect active Grafana Golden Signals dashboard: [http://localhost:3000](http://localhost:3000).
2. Check Prometheus error breakdown:
   ```promql
   sum by (alarm_status) (rate(telemetry_anomalies_detected_total[10m]))
   ```
3. Inspect Kubernetes pod status and logs:
   ```bash
   kubectl get pods -n telemetry-system -l app.kubernetes.io/name=hybrid-telemetry-pipeline
   kubectl logs -n telemetry-system -l app.kubernetes.io/name=hybrid-telemetry-pipeline --tail=100
   ```
4. If pods are restarting, check exit codes:
   ```bash
   kubectl describe pods -n telemetry-system -l app.kubernetes.io/name=hybrid-telemetry-pipeline | grep -A 5 "Last State"
   ```

#### Remediation:
- If CPU throttling is observed: Manually scale the deployment up while investigating root cause:
  ```bash
  kubectl scale deployment hybrid-telemetry-pipeline -n telemetry-system --replicas=6
  ```
- If a specific sensor channel is malfunctioning: Update ConfigMap to isolate the channel or adjust noise filters, then trigger rolling restart:
  ```bash
  kubectl rollout restart deployment/hybrid-telemetry-pipeline -n telemetry-system
  ```

---

### 2. Alert: `CryogenicQuenchImminent`
- **Severity**: Critical (P1 - Immediate Physical Safety)
- **Condition**: `telemetry_cryo_temperature_kelvin > 4.2` for $> 5\text{ seconds}$.
- **Impact**: Superconducting dipole magnet is transitioning to normal resistive state. High risk of thermal destruction due to megajoule stored inductive energy.

#### Diagnostics & Triage:
1. Identify affected magnet sector:
   ```promql
   telemetry_cryo_temperature_kelvin > 4.2
   ```
2. Verify automated interlock beam dump status:
   ```promql
   telemetry_beam_intensity_protons
   ```
   *Beam intensity must drop to zero within 3 beam revolutions ($< 270\,\mu\text{s}$).*

#### Remediation:
1. Confirm hardware energy extraction systems (quench heater firing and extraction resistors) have automatically engaged.
2. Escalate immediately to Cryogenics & Magnet Protection on-call engineer.
3. Lock beam injection interlock until cryo recovery cycle reaches $< 1.9\,\text{K}$.

---

### 3. Alert: `DSPProcessingLatencyP99Breached`
- **Severity**: Warning (P3 - Ticket)
- **Condition**: $P_{99}$ signal processing latency $> 25\text{ms}$ for $> 1\text{ minute}$.
- **Impact**: Risk of buffer queue buildup and dropped telemetry samples.

#### Diagnostics & Triage:
1. Check CPU throttling metrics in Kubernetes:
   ```promql
   sum(rate(container_cpu_cfs_throttled_periods_total{container="telemetry-pipeline"}[5m]))
   ```
2. Inspect buffer fill ratio:
   ```promql
   telemetry_ring_buffer_fill_ratio
   ```

#### Remediation:
1. Verify if HPA is triggering scale-out:
   ```bash
   kubectl get hpa -n telemetry-system
   ```
2. If HPA is pinned at `maxReplicas`: Increase `maxReplicas` in `k8s/base/hpa.yaml` or increase CPU limits in `deployment.yaml`.

---

### 4. Alert: `TelemetryPipelineInstanceDown`
- **Severity**: Critical (P1 - Page)
- **Condition**: `up{job="hybrid-telemetry-pipeline"} == 0` for $> 15\text{ seconds}$.

#### Diagnostics:
1. Check kubelet events:
   ```bash
   kubectl get events -n telemetry-system --sort-by='.metadata.creationTimestamp'
   ```
2. Test probe endpoints directly via port-forward:
   ```bash
   kubectl port-forward -n telemetry-system svc/hybrid-telemetry-pipeline 8080:8080 9102:9102
   curl -i http://localhost:8080/healthz
   curl -i http://localhost:8080/readyz
   curl -i http://localhost:9102/metrics
   ```

---

## 🔄 Routine Operations & Deployment Verification

### Verifying Canary Deployment
```bash
# Check rollout progress
kubectl rollout status deployment/hybrid-telemetry-pipeline -n telemetry-system

# Rollback if error budget burns during rollout
kubectl rollout undo deployment/hybrid-telemetry-pipeline -n telemetry-system
```
