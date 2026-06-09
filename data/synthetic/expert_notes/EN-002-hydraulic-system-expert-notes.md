# EN-002: Expert Notes — Hydraulic Power Unit Maintenance

**Document ID:** EN-002  
**Source:** Interview with Lead Hydraulics Technician, Chicago Facility  
**Asset Class:** Hydraulic Power Units (hydraulic_01)  
**Relates To:** SOP-MAINT-002

---

## Filter Life and Replacement Triggers

The primary trigger for filter replacement is differential pressure (dP) exceeding 2.5 bar
across the filter element (SCADA tag: hydraulic_01/filter_dp_bar). Once dP climbs past
2.0 bar you're getting close — plan the replacement within the next shift.

The 2000-hour PM schedule is the backstop. In our Chicago facility, filters typically
reach the dP limit around 1600–1800 hours due to the fine metal fines from machining
operations. If oil analysis shows particulate count above ISO 16/14/11, replace immediately
regardless of dP or hours.

## Contamination Causes and Effects

Most filter clogs here come from:
1. Metallic fines from the hydraulic cylinder rods (40% of cases)
2. External contamination during oil top-up — always use a filtered fill cart
3. Seal degradation sending rubber particles into the system

If you pull the old element and see bright metallic particles, there's a component wearing
upstream — check the cylinder seals and pump vanes before reassembling.

## Depressurization — Do It Right

The most dangerous step is skipping proper depressurization. hydraulic_01 runs at 200 ± 5 bar
operating pressure. The accumulators hold pressure even after the pump stops — hold the
manual bleed valve open for a full 30 seconds and watch the gauge. It must read 0 bar
before you touch any hydraulic connection. Never rely on indicator lights alone; always
verify on the gauge.

Oil temperature must be below 50°C before draining. Opening a hot hydraulic line at 80°C
results in flash burns. The hydraulic unit takes about 20 minutes to cool after shutdown.

## Filter Bowl and O-ring

The filter bowl torque is 35 Nm — not "hand tight plus a bit." Use a torque wrench.
Under-torquing causes seepage; over-torquing cracks the bowl.

Always replace the O-ring when replacing the element. We use the element kit that includes
the O-ring (part HPU-FILTER-KIT-01); buying elements separately often means the O-ring
gets reused and fails.

After reassembly, start the pump, let it reach operating pressure (200 bar), and verify
the filter dP reads below 0.5 bar. Any reading above 0.5 bar at temperature suggests
the element wasn't seated correctly or the bowl wasn't torqued.

## Drain Pan Requirement

Always use a drain pan with minimum 5 L capacity. hydraulic_01 filter housing holds
about 2–3 L. Have the spill kit within arm's reach — slippery hydraulic oil on a concrete
floor is a slip hazard.

## System Pressure After Maintenance

Normal operating pressure is 200 ± 5 bar. If pressure fails to reach 195 bar after
filter replacement, check for a stuck relief valve — we've had two cases where a relief
valve stuck open after a maintenance cycle. If system pressure is restored but the
hydraulic circuit doesn't hold pressure under load, the check valve may need inspection.

## FMEA Reference

Filter clog failure mode is FM-HYD-003. The consequence of ignoring a high dP is bypass
valve opening and unfiltered oil circulating through the system — accelerated wear of the
pump and actuators. We had a pump failure in 2024 traced directly to running the system
for 8 hours with the filter bypass valve open.
