# Rural Delivery Droid - Anti-Tamper & Security Logging Flow

This Node-RED flow listens for unauthorized physical access attempts and intrusion alerts from rural delivery droids, classifies incident severity, appends tamper-evident audit records to a local log file, and automatically transmits emergency lockdown countermeasures to the droid.

---

## 1. Monitored Security Threats

1. **Compartment Forced / Pried Open (`CRITICAL`):**
   - Triggered when the magnetic door reed switch opens while the electronic lock status is `LOCKED`.
2. **Multiple Unauthorized RFID/NFC Scans (`HIGH`):**
   - Triggered when an unrecognized card/phone is scanned 3 or more times consecutively.
3. **Chassis & Maintenance Hull Intrusion (`CRITICAL`):**
   - Triggered when enclosure tamper limit switches break loop while the droid is on route.
4. **Severe Shock or Rollover / Vehicle Lift (`WARNING` / `HIGH`):**
   - Detected via the onboard 6-axis IMU / accelerometer when shock > 3.0G or tilt angle > 45°.

---

## 2. Telemetry Alert Payload Format

Droids publish to `droid/<droid_id>/tamper` (e.g., `droid/droid-alpha-01/tamper`):

```json
{
  "droid_id": "droid-alpha-01",
  "timestamp": "2026-11-02T12:00:00Z",
  "event_type": "COMPARTMENT_PRIED_OPEN_WHILE_LOCKED",
  "reason": "Reed switch opened without authorized RFID scan",
  "sensors": {
    "compartment_switch": "BREACHED",
    "door_switch": "OPEN",
    "rfid_failed_count": 0,
    "vibration_g": 4.2,
    "imu_tilt_deg": 12
  },
  "location": {
    "latitude": -29.8587,
    "longitude": 31.0218,
    "altitude_m": 124.5
  },
  "battery_soc_pct": 86
}
```

---

## 3. Automated Incident Pipeline

```
[droid/+/tamper] (TLS Port 8883)
         │
         ▼
[Parse JSON Alert]
         │
         ▼
[Triage & Enrich Incident]
  - Assigns unique Incident ID (e.g., INC-M7K2P8)
  - Classifies Severity (CRITICAL, HIGH, WARNING)
  - Evaluates automated response triggers
         │
         ├──────────────────────────────────────────────┐
         ▼                                              ▼
[Append to anti_tamper_audit.log]         [Publish Droid Lockdown (TLS)]
  - Persistent JSONL record with GPS        - Topic: droid/<droid_id>/command/lockdown
  - Stores timestamp, sensors, severity     - Action: secondary deadbolt, alarm siren,
                                              strobe LEDs, camera snapshot
```

---

## 4. Audit Log Output

Records are continuously appended to:
`C:/Users/mubay/OneDrive/Documentos/egrocca certificates/node_red_tamper_system/logs/anti_tamper_audit.log`

Each line contains a complete incident snapshot ready for security forensics or fleet dashboard ingestion.

