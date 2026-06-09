# EN-001: Expert Notes — Induction Motor Maintenance

**Document ID:** EN-001  
**Source:** Interview with Senior Mechanical Technician, Chicago Facility  
**Asset Class:** Induction Motors (motor_01, motor_02)  
**Relates To:** SOP-MAINT-001

---

## Bearing Failure Detection

From 15 years of working with the AC induction motors here, vibration RMS is the leading
indicator. The alarm threshold is 4.5 mm/s — when you see that, bearings are the first
thing to check. Temperature above 90°C at the bearing housing confirms it. Don't wait
for both; either one alone is enough to pull the motor.

The early signs before you hit those thresholds:
- A slight grinding or ticking at low load — easy to miss in a noisy facility
- Grease leaking from the end caps, often brownish-black and burnt-smelling
- Intermittent vibration spikes that the SCADA historian shows but operators dismiss

## Bearing Installation Tips

Use the induction heater — never hammer bearings on cold. Heat to 80–100°C; the bearing
slips on the shaft almost by itself. Higher than 100°C risks softening the bearing steel.
The TOOL-HEAT-01 induction heater we use has a built-in thermostat; set it to 90°C and
wait for the beep.

Always wear nitrile gloves during handling — even a fingerprint's worth of skin oil can
cause premature corrosion on the race. The grease is Mobil Polyrex EM; apply sparingly to
the inner race. Do not over-grease — 30–50% fill is correct; over-greased bearings run
hot.

Drive-end bearing is the 6310-2RS (part BRG-6310-2RS); non-drive end is the smaller
6208-2RS (part BRG-6208-2RS). Don't mix them up — the 6310 carries higher radial load.

## Precision Alignment

After reinstallation, alignment tolerance is < 0.05 mm TIR (Total Indicator Reading). We
use a dial indicator on a magnetic base. Measure both parallel and angular misalignment;
shimming is usually faster than moving the motor base.

If you can't get below 0.10 mm TIR on first attempt, check the motor foot bolts and
coupling hub bores. Most "misalignment" problems I've seen are actually loose hardware.

## Run-In Procedure

Always run uncoupled for 15 minutes first. Listen for roughness, watch the vibration
trend: it should drop below 2.5 mm/s within 5 minutes of spin-up. Temperature rise
across the bearing housing should be less than 40°C above ambient.

Only couple to load after uncoupled run passes. Then run at full load for 30 minutes,
verify vibration stays < 2.5 mm/s, and document in CMMS.

## Two-Person Rule

For motors above 5.5 kW, always work with a second technician present. It's a facility
safety rule, not optional. motor_01 and motor_02 are both 22 kW — never work on them alone.

## FMEA Reference

The bearing wear failure mode is documented under FM-MOT-001. Most bearing failures here
have been due to over-greasing (about 40%) or misalignment after previous maintenance
(about 35%). The remaining 25% are true wear-out at end of bearing life.
