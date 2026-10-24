# Copper evaluation — stopped; historical four-layer results

**Decision (2026-10-25): use two layers, 1 oz copper. Copper/thermal qualification
was stopped at the user’s instruction. The results below describe the old
four-layer design only and do not qualify the selected two-layer board.
No further thermal work is scheduled.**

Rollback checkpoint: **`62ef1ea`**. Native PCB, schematic, placement and stackup
remain unchanged. This report supersedes and withdraws the earlier
12 A-per-phase rejection.

**The electrical estimates are below budget, but no option has a completed
per-neck thermal qualification. No copper option is selected.** In particular,
the 1 oz / 0.5 oz option must not be called passing merely because the isolated
phase calculation and plane-resistance calculation pass their individual screens.

## Requirements and ordered results

Shared input, fuse path, 12 V distribution and GND return: **12 A total**.
Each Mini's supply/return branch and each motor phase: **2.5 A**. Heating current
is RMS. Maximum copper temperature rise: **20 °C**. Maximum supply-loop drop:
**0.3 V excluding F1 holder and fuse**, per the user's revised instruction.
Six simultaneous 2.5 A rail loads would be 15 A and are outside this envelope.

| Order | Outer / inner | Finished outer / inner copper | Isolated 1 mm phase rise at 2.5 A | Estimated worst copper + Mini contacts | Complete thermal result |
|---|---|---|---:|---:|---|
| 1 | 1 oz / 0.5 oz | 35 / 15.2 µm | 14.30 °C | 0.1451 V | Unresolved |
| 2 | 1 oz / 1 oz | 35 / 30 µm | 14.30 °C | 0.1079 V | Unresolved |
| 3 | 2 oz / 2 oz | 70 / 61 µm | 7.15 °C | 0.0885 V | Unresolved |

These are screening results, **not three thermal failures**. Options 2 and 3 use
the same extracted electrical geometry with sheet resistance scaled by finished
copper thickness; this is not a new thermal simulation. No first full pass has
been established. The first option received the detailed two-resolution DC
analysis below. There is no evidence here that 2 oz is necessary or sufficient.

The 18 actual phase paths are all 1.000 mm wide on L1 and 30.683–36.283 mm long.
The isolated-conductor calculation uses the Brooks/Adam fit to IPC-2152 data:

`ΔT = 215.3 × I² × W_mil^(-1.15) × thickness_mil^(-1)`

It does not include adjacent phase heating, Mini dissipation or holder heat.
No unverified plane-cooling factor has been applied.
[KiCad's published formula](https://docs.kicad.org/doxygen/tracks__width__versus__current__formula_8h.html)
and [IPC's discussion of plane cooling and thermal interaction](https://www.ipc.org/system/files/technical_resource/E7%26S22_03.pdf).

## Actual filled-plane voltage-drop calculation

The exported native L3 `12V_IN` and `12V_FUSED` polygons and L2 GND polygon are
solved as resistive sheets, retaining antipads and filled-copper constrictions.
Each soldered pad is an ideal equipotential boundary. The two legs of each fuse
terminal are connected at that terminal. The model does not connect the two fuse
terminals through copper: their separately reported series drop is excluded.
Only L2 is credited for return current; F.Cu/B.Cu GND and additional control-header
GND contacts are omitted. No fictitious 12 A current is imposed on low-current
encoder GND traces.

Copper resistivity is 1.724e-8 Ω·m at 20 °C, scaled by 0.00393/°C to an assumed
**40 °C copper temperature**. This is a resistance assumption, not a temperature
prediction. A hotter ambient requires resistance rescaling. Nominal finished
inner copper is 15.2 µm for the first option, from JLC's published stackup.

Six-port transfer-resistance matrices allow each axis's drop to be maximized
subject to `0 ≤ I_axis ≤ 2.5 A` and `sum(I_axis) = 12 A`. The maximizing load may
differ for each row; these are separate worst-case load configurations.

| Axis | Plane-only worst drop, 0.125 mm grid | Plane-only worst drop, 0.25 mm grid |
|---|---:|---:|
| 1 | 64.644 mV | 65.068 mV |
| 2 | 65.967 mV | 66.398 mV |
| 3 | 67.966 mV | 68.435 mV |
| 4 | 71.211 mV | 71.711 mV |
| 5 | 73.605 mV | 74.147 mV |
| 6 | **74.766 mV** | **75.307 mV** |

Worst electrical axis is also the farthest, **axis 6**. Its maximizing rail loads
are `[0, 2, 2.5, 2.5, 2.5, 2.5] A`. Equal 2 A loads produce 71.116 mV at axis 6
on the fine grid. The two worst-drop results differ by **0.541 mV (0.72%)**.
Use the larger 75.307 mV estimate for budgeting. This mesh comparison is not a
mathematical error bound on arbitrarily small copper features.

Additional allowances:

- **19.755 mV barrels:** 1.6 mm full-board traversal; 18 µm assumed barrel copper;
  two 1.3 mm input holes at 12 A, one 1.65 mm F1 leg on each side carrying all
  12 A, and two 1.101 mm Mini power holes at 2.5 A. No solder conductivity credit.
  This intentionally does not depend on equal current sharing between F1 legs.
- **50 mV Mini contacts:** two power receptacle contacts × 10 mΩ × 2.5 A, as
  instructed. No manufacturer resistance is claimed.
- Total: **145.062 mV**, leaving **154.938 mV** to the 0.3 V limit.

JLC currently publishes **18 µm average** hole plating; that is not a guaranteed
minimum at every point. The estimate is conditional on that assumed thickness.
Manufacturing thickness tolerances, solder/contact details and wire-contact
resistance in J5 are not independently bounded. At 12 A the remaining allowance
would accommodate **12.91 mΩ total for both J5 wire contacts**; this is a budget,
not a Phoenix datasheet specification. The copper budget runs from J5 solder
pads to the Mini and back; the additional Mini contacts are included explicitly.
[JLC capabilities](https://jlcpcb.com/capabilities/Capabilities).

## Per-neck coverage and unresolved thermal work

The DC solver accounts electrically for constrictions throughout the filled
planes, but **does not calculate their temperatures**. Terminal-exit geometry
was separately measured 0.01 mm outside each power pad. Available copper arc
length is a geometric diagnostic, not the width of a straight IPC test trace:

| Terminal exits | Count | Current envelope | Available copper arc at each exit |
|---|---:|---:|---:|
| J5 input / return | 2 | 12 A each | 8.231 mm |
| F1, two legs per terminal | 4 | 12 A total per pair; sharing not assumed | 9.488 mm |
| J11–J16 VIN | 6 | 2.5 A each | 7.603 mm |
| J11–J16 power GND | 6 | 2.5 A each | 7.603 mm |

All 18 measured exits have continuous copper around that sampled circle; none
uses thermal spokes. This **does not constitute an exhaustive per-neck thermal
check**. Radial current crowding inside the annular pads, plated barrels, narrow
paths between nearby antipads, and the simultaneous thermal contribution of the
other conductors must be included before asserting every neck stays below 20 °C.
Converting these short radial escapes into a long-strip width and treating its
IPC chart result as the actual temperature would be unsupported.

Still unsatisfied:

1. Complete per-neck IPC-2152 thermal qualification of shared input/fuse copper,
   the power distribution and GND return, including pad/barrel current crowding.
2. Coupled temperature-rise assessment of adjacent phase traces and module/holder
   heating. The isolated 14.30 °C result alone is insufficient for this.
3. Input-terminal/holder/receptacle temperature rise at the specified currents.
   A current rating or assumed contact resistance alone does not establish
   ≤20 °C rise. Holder resistance alone implies 0.72 W at 12 A.

A coupled thermal analysis with declared board/assembly boundary conditions, or
representative steady-state measurements, is needed to close these gaps. The
present scripts provide electrical data and isolated IPC-based screens only.

## F1 and fuse — outside the copper budget

**Holder assumption:** 5 mΩ total for the complete Keystone 3557-2 holder's
contacts, as instructed; **60 mV and 0.72 W at 12 A**. It is not 5 mΩ per blade,
and it is not a value found in Keystone's drawing or catalog.
[Keystone 3557-2 drawing](https://www.keyelco.com/product-pdf.cfm?p=296).

The requested Littelfuse 257-series datasheet gives these **typical voltage drops
at rated current**, not maximum limits. No fuse rating is selected by this table:

| Example 257 fuse rating | Datasheet typical drop at that rating | Plus 60 mV holder allowance at the carrier's 12 A |
|---|---:|---:|
| 15 A | 102 mV | 162 mV |
| 20 A | 98 mV | 158 mV |
| 25 A | 92 mV | 152 mV |
| 30 A | 84 mV | 144 mV |

The last column is a reporting allowance combining the requested rated-current
fuse figure with the 12 A holder assumption. It is **not a measured or guaranteed
combined drop at 12 A**. Fuse temperature and resistance vary with current.
For example, adding the 15 A example allowance to option 1's electrical estimate
gives approximately 0.307 V including those excluded components. This does not
violate the revised copper-only budget and does not select a 15 A fuse.
**Fuse rated to the connected supply** remains the BOM/README rule.
[Littelfuse 257-series manufacturer datasheet, archived by DigiKey](https://media.digikey.com/pdf/Data%20Sheets/Littelfuse%20PDFs/257%20Series.pdf).

## Price and reproducibility

JLC's live quote on 2026-10-25 for **five 160 × 120 mm, 1.6 mm, four-layer,
1 oz / 0.5 oz boards, green, white silkscreen, lead-free HASL** is **US$42.40**
(board manufacture only; excludes shipping, tax and assembly). This is a
candidate quote, **not a selected passing option**. No order was created or
fabrication data uploaded.
[Quote screenshot](../../pcb/archive/copper-evaluation/quote-1oz-0.5oz.png).

Outputs and reproducible analysis:

- [Corrected machine-readable report](../../pcb/archive/copper-evaluation/copper-options-review.json).
- [Geometry export](../../pcb/archive/copper-evaluation/scripts/export_planes.py), run with KiCad Python.
- [Plane DC solver](../../pcb/archive/copper-evaluation/scripts/plane_dc.py), run with Python 3 plus numpy,
  scipy, shapely and pyamg, once with argument `0.25`, then `0.125`.
- [Screen/report generator](../../pcb/archive/copper-evaluation/scripts/evaluate_copper.py), run with KiCad Python.
- [Source and quote provenance](../../pcb/archive/copper-evaluation/provenance.json).

The report verifies the board hash matches the exported geometry. Native PCB
and schematic are unchanged from the committed ERC/strict-DRC-clean checkpoint;
no claim is made that ERC or DRC proves thermal performance.
