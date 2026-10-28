"""compliance_engine.py — Layer 1. Pure functions. NO model calls.
If `import anthropic` appears in this file, you have failed the week."""


from dataclasses import dataclass
from enum import Enum
import pytest
from capstone_data import LOADS, EVENTS, NOW_TS, CARRIERS, LANES

class FindingType(Enum):
   LATE_PICKUP    = "late_pickup"      # actual > scheduled + threshold
   NO_SHOW_RISK   = "no_show_risk"     # no carrier ping near the window
   MISSING_GPS    = "missing_gps"      # assigned truck, silent tracker
   DETENTION_RISK = "detention_risk"   # arrived far too early
   REPEAT_OFFENDER= "repeat_offender"  # carrier ≥3 late pickups in window

class Severity(Enum):
   INFO = "info"; WATCH = "watch"; ACT = "act"

@dataclass(frozen=True)
class Finding:
   load_id: str
   finding_type: FindingType
   severity: Severity
   evidence: dict      # the numbers that prove it — the narrative may
                     # only use numbers that appear here

# rule -> pickup_complete.ts > window_end + 30*60
def classify_late_pickup(loads, events, now_ts) -> list[Finding]:
   findings = []
   # storing all the pickups 
   pickups = []
   for e in events:
      if e["type"] == "pickup_complete":
         pickups.append({"lid": e["load_id"], "pickup_ts": e["ts"]})

   # pickup info   
   for p in pickups:
      load_id = p["lid"]
      load = loads[load_id]
      window_end = load.get("window_end", 0)
      threshold = window_end + 30*60
      pickup_complete_ts = p["pickup_ts"]

      if pickup_complete_ts > threshold:
         late_by_min = (pickup_complete_ts - window_end) // 60
         evidence = {"late_by_min": late_by_min, "pickup_complete_ts": pickup_complete_ts, "window_end": window_end}
         findings.append(Finding(load_id=load_id, finding_type=FindingType.LATE_PICKUP, severity=Severity.ACT, evidence=evidence))

   return findings

# rule -> if status == assigned and NOW_TS >= window_start, and no arrived or pickup_complete event, and no gps_ping in [window_start − 3H, NOW_TS]
def classify_no_show_risk(loads, events, now_ts) -> list[Finding]: 
   findings = []
   H = 3600
   
   for load_id, load in loads.items():
      if load["status"] == "assigned" and now_ts >= load["window_start"]:
         window_start = load["window_start"]
         gps_window_start = window_start - 3 * H
         
         # checking if the load has been picked up / arrived or got a gps ping
         has_pickup_event = False
         latest_gps_ts = None
         
         for e in events:
            if e["load_id"] == load_id:
               if e["type"] in ["arrived", "pickup_complete"]:
                  has_pickup_event = True
               if e["type"] == "gps_ping" and gps_window_start <= e["ts"] <= now_ts:
                  latest_gps_ts = e["ts"]
         
         if not has_pickup_event and latest_gps_ts is None:
            evidence = {"window_start": window_start, "lookback_hours": 3}
            findings.append(Finding(load_id=load_id, finding_type=FindingType.NO_SHOW_RISK, severity=Severity.WATCH, evidence=evidence))
   
   return findings

# rule -> is status == in_transit and (no gps_ping at all or latest ping older than NOW_TS − 6H)
def classify_missing_gps(loads, events, now_ts) -> list[Finding]:
   findings = []
   H = 3600
   ts_condition = now_ts - 6*H

   for load_id, load in loads.items():
      latest_ping = None
      if load["status"] == "in_transit":
         for e in events:
            if e["type"] == "gps_ping" and e["load_id"] == load_id:
               latest_ping = e["ts"] 
         if latest_ping == None or latest_ping < ts_condition:
            evidence = {"latest_ping": latest_ping}
            findings.append(Finding(load_id=load_id, finding_type=FindingType.MISSING_GPS, severity=Severity.WATCH, evidence=evidence))

   return findings

# rule -> arrived.ts < window_start - 2H
def classify_detention_risk(loads, events, now_ts) -> list[Finding]:
   findings = []
   H = 3600
   for e in events:
      if e["type"] == "arrived":
         id = e["load_id"]
         ts = e["ts"]
         load = loads.get(id, 0)
         window_start = load["window_start"]
         condition = window_start - 2*H
         if ts < condition:
            evidence = {"arrived_ts": ts, "window_start": window_start, "lookback_hours": 2}
            findings.append(Finding(load_id=id, finding_type=FindingType.DETENTION_RISK, severity=Severity.WATCH, evidence=evidence))

   return findings

# rule -> a carrier with >= 3 LATE_PICKUP findings
def classify_repeat_offender(loads, events, now_ts, carriers, findings) -> list[Finding]:
   findings_new = []
   late_carriers = []

   # collecting all the carrier ids who have late pickups 
   for f in findings:
      if f.finding_type == FindingType.LATE_PICKUP:
         id = f.load_id
         load = loads.get(id, 0)
         late_carriers.append(load["carrier_id"])
   
   for c in carriers:
      if late_carriers.count(c) >= 3:
         evidence = {"carrier_id": c}
         findings_new.append(Finding(load_id=c, finding_type=FindingType.REPEAT_OFFENDER, severity=Severity.WATCH, evidence=evidence))

   return findings_new

def scan(loads, events, carriers, now_ts) -> list[Finding]:
   # todo: run every classifier; return all findings, deterministically
   # sorted. Same inputs MUST produce byte-identical output, every time.

   findings = []

   f_late_pickup = classify_late_pickup(loads, events, now_ts)
   findings.extend(f_late_pickup)
   f_no_show_risk = classify_no_show_risk(loads, events, now_ts)
   findings.extend(f_no_show_risk)
   f_detention_risk = classify_detention_risk(loads, events, now_ts)
   findings.extend(f_detention_risk)
   f_missing_gps = classify_missing_gps(loads, events, now_ts)
   findings.extend(f_missing_gps)
   f_repeat_offender = classify_repeat_offender(loads, events, now_ts, carriers, findings)
   findings.extend(f_repeat_offender)

   return findings


if __name__ == "__main__":
   # quick sanity check: run the engine on the capstone data, print findings
   findings = scan(LOADS, EVENTS, CARRIERS, NOW_TS)
   for f in findings:
      print(f)
      print()