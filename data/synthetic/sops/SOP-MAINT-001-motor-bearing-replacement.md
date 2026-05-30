# SOP-MAINT-001: Induction Motor Bearing Replacement

**Document ID:** SOP-MAINT-001  
**Revision:** 2.1  
**Asset Class:** Induction Motor (ISO 14224 Class: Rotating Equipment)  
**Applies To:** motor_01, motor_02, and all AC induction motors at Chicago facility

---

## 1. Purpose

This procedure describes the safe replacement of worn or failed bearings in AC induction
motors rated up to 75 kW. It is triggered when vibration RMS exceeds 4.5 mm/s or bearing
temperature exceeds 90°C.

## 2. Required Skills

- Electrical Journeyman (NFPA 70E qualified)
- Mechanical Technician Level 2

## 3. Safety Precautions

1. **LOTO required** — De-energize and lock out/tag out all energy sources before beginning.
2. Verify zero energy state with calibrated voltmeter.
3. Allow motor to cool to ambient temperature before handling.
4. Wear nitrile gloves when handling bearings (prevent contamination from skin oils).
5. Do not work alone — a second technician must be present for motors > 5.5 kW.

## 4. Parts and Tools

| Item | Part Number | Quantity |
|------|------------|---------|
| Bearing, Drive End (6310-2RS) | BRG-6310-2RS | 1 |
| Bearing, Non-Drive End (6208-2RS) | BRG-6208-2RS | 1 |
| Bearing puller set | TOOL-PULL-01 | 1 |
| Induction heater | TOOL-HEAT-01 | 1 |
| Bearing grease (Mobil Polyrex EM) | LUB-POLYREX | 1 tube |

## 5. Procedure

1. Complete LOTO documentation in CMMS (work order required).
2. Disconnect motor from driven equipment; record coupling alignment readings.
3. Remove motor from mounting; transport to maintenance bay.
4. Disassemble motor: remove end caps, rotor, and worn bearings using puller.
5. Clean shaft and housing bores; inspect for scoring.
6. Heat new bearings to 80-100°C using induction heater; install on shaft.
7. Reassemble motor; verify bearing clearance.
8. Reinstall on equipment; perform precision alignment (< 0.05 mm TIR).
9. Run uncoupled for 15 minutes; verify vibration < 2.5 mm/s, temperature rise < 40°C.
10. Couple to load; run at full load for 30 minutes; document final readings in CMMS.

## 6. Acceptance Criteria

- Vibration RMS: < 2.5 mm/s (ISO 10816-3 Class II)
- Bearing temperature: < 70°C above ambient
- No audible roughness or impact noise

## 7. References

- OEM Manual: ABB Motors M2BAX Series, Doc No. 3GZF500870-85
- FMEA Reference: FM-MOT-001 (Bearing Wear)
- ISO 10816-3: Mechanical vibration — Evaluation of machine vibration
