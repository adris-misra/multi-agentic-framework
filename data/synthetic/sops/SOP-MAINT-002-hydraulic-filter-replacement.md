# SOP-MAINT-002: Hydraulic Filter Element Replacement

**Document ID:** SOP-MAINT-002  
**Revision:** 1.3  
**Asset Class:** Hydraulic Power Unit (ISO 14224 Class: Fluid Systems)  
**Applies To:** hydraulic_01 and all HPUs at Chicago facility

---

## 1. Purpose

Replace the hydraulic filter element when differential pressure (dP) across the filter
exceeds 2.5 bar, or on a 2000-hour preventive maintenance schedule.

## 2. Trigger Conditions

- Filter dP > 2.5 bar (alarm from SCADA tag: hydraulic_01/filter_dp_bar)
- 2000-hour PM schedule
- Oil analysis indicates particulate count > ISO 16/14/11

## 3. Safety Precautions

1. **De-pressurize system** before opening any hydraulic connection.
2. Verify system pressure = 0 bar using gauges; do NOT rely on indicator lights alone.
3. Allow oil to cool below 50°C before draining.
4. Wear face shield and chemical-resistant gloves.
5. Have oil spill kit available within 3 meters.

## 4. Procedure

1. Open work order in CMMS; record current filter dP and operating hours.
2. Shut down hydraulic pump; engage emergency stop.
3. Depressurize accumulators using manual bleed valve (30-second hold).
4. Confirm pressure = 0 bar on all gauges.
5. Place drain pan (minimum 5L) under filter housing.
6. Remove filter bowl; extract and inspect old element (note contamination type).
7. Clean bowl with lint-free cloth; inspect O-ring and sealing surfaces.
8. Install new element; lubricate O-ring with clean hydraulic oil.
9. Reinstall bowl; torque to 35 Nm.
10. Start pump; check for leaks; verify dP < 0.5 bar.
11. Record replacement in CMMS; attach photo of old element condition.

## 5. Acceptance Criteria

- Filter dP: < 0.5 bar at operating temperature
- No leaks at filter connections
- System pressure restored to 200 ± 5 bar

## 6. FMEA Reference

- FM-HYD-003 (Filter Clog / Bypass) — Failure Mode: gradual pressure drop increase,
  potential bypass valve opening, contaminated oil circulating through system.
