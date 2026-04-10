# Battery-Cooling-Project
# 🔋 Serpentine Liquid Cooling System for Li-ion Battery Packs
### Python-Coupled CFD Simulation | ANSYS Fluent + PyFluent Automation

<div align="center">

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat&logo=python&logoColor=white)
![ANSYS](https://img.shields.io/badge/ANSYS-Fluent-FFB71B?style=flat&logo=ansys&logoColor=black)
![SolidWorks](https://img.shields.io/badge/SolidWorks-CAD-C00000?style=flat)
![License](https://img.shields.io/badge/License-Academic-green?style=flat)

**Trakya University — Faculty of Engineering | Graduation Project 2024–2025**

</div>

---

## 📋 Overview

This project develops a complete **Battery Thermal Management System (BTMS)** for a 24-cell 21700 lithium-ion battery pack. A serpentine cold plate was designed, simulated across three discharge rates (1C / 3C / 5C), and optimised through a **fully automated Python parametric sweep** — eliminating manual bottlenecks and reducing study time by ~70%.

The system meets **IEC 62660** and **ISO 6469** thermal safety standards under all evaluated conditions.

---

## ⚡ Key Results

| Metric | Value |
|--------|-------|
| T_max @ 5C optimised | **317.2 K (44 °C)** ✅ |
| T_avg @ 5C optimised | **304.3 K** |
| T_max @ 5C baseline (unoptimised) | **353.8 K (80.7 °C)** ❌ |
| Pressure drop — optimised design | **1957 Pa @ 0.4 m/s** |
| ΔP reduction via width sweep | **23.6% (4.0 → 4.5 mm)** |
| Simulation time reduction | **~70% via Python automation** |

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| **ANSYS Fluent** | CFD solver — conjugate heat transfer (CHT) |
| **ANSYS Meshing** | Unstructured mesh + inflation layers |
| **SolidWorks** | 3D CAD geometry (serpentine cold plate + cell array) |
| **SpaceClaim** | Geometry prep and Named Selection assignment |
| **Python 3** | Automation controller |
| **PyFluent API** | Solver execution + results extraction |
| **SolidWorks API** | Parametric geometry modification |
| **SpaceClaim API** | Named selection re-assignment post-import |

---

## 🔁 Python Automation Pipeline

The core innovation of this project is a fully automated design-to-result loop. Python modifies **geometric design parameters directly in SolidWorks** — not just file conversion.

```
SolidWorks API          SpaceClaim API        Fluent Meshing         PyFluent API           Python Loop
─────────────────       ──────────────────    ──────────────────     ──────────────────     ──────────────
Modify channel width  → Import STEP         → Replay mesh journal → Set BCs + Run solver → Next parameter
Rebuild model           Re-assign Named       Inflation layers       Extract T_max, T_avg   Repeat
Export STEP             Selections            BOI refinement         ΔP, T_out
```

### What the script automates:
1. **Geometry** — Modifies channel width / bend radius / wall thickness in `.sldprt` via SolidWorks API, rebuilds, exports STEP
2. **Preparation** — Imports STEP in SpaceClaim, re-assigns Named Selections (inlet, outlet, wall, cell surfaces) lost during conversion
3. **Meshing** — Replays pre-recorded Fluent Meshing journal — consistent mesh every iteration
4. **Solving** — Sets inlet velocity or mass flow rate via PyFluent, runs steady-state solver, monitors convergence
5. **Extraction** — Pulls T_max, T_avg, T_out, ΔP from converged solution
6. **Loop** — Increments parameter and repeats — fully unattended

---

## 🔧 System Design

### Battery Pack
- **24 × 21700 cylindrical LiFePO₄ cells** in a 4×6 matrix
- Cell dimensions: Ø 21 mm × 70 mm, C_nom = 4 Ah, R_int ≈ 0.02 Ω
- Uniform 6 mm inter-cell spacing

### Serpentine Cold Plate
| Parameter | Value |
|-----------|-------|
| Channel cross-section | 4.5 mm × 12.5 mm (rectangular) |
| Hydraulic diameter D_h | 6.15 mm |
| Bend radius | 13.5 mm (≥ 2 × D_h) |
| Wall thickness | ~1 mm aluminium |
| Number of channels | 4 parallel serpentine |
| Plate material | Aluminium |
| Coolant | 50/50 water–ethylene glycol |

---

## 📐 CFD Setup

| Parameter | Value |
|-----------|-------|
| Solver | ANSYS Fluent — steady-state |
| Flow regime | Laminar (Re ≈ 60, confirmed analytically) |
| Near-wall mesh | 15 inflation layers, y⁺ < 5 |
| Convergence — energy | Residual ≤ 10⁻⁶ |
| Convergence — momentum | Residual ≤ 10⁻⁴ |
| Heat source (1C / 3C / 5C) | 20,000 / 180,000 / 500,000 W/m³ |

### Heat Generation
```
Q_irr = I² × R_int   (Joule heating — dominant term)
Q_rev = T × dE/dT × I   (entropic heat — secondary)

5C discharge: I = 20 A → Q_irr = 8.0 W/cell → 193.4 W total (24 cells)
```

---

## 📊 Simulation Results

### Multi-C-Rate Comparison

| Scenario | T_max (K) | T_avg (K) | ΔP (Pa) | Status |
|----------|-----------|-----------|---------|--------|
| 1C — baseline | 296.2 | 295.1 | 62 | ✅ Safe |
| 3C — baseline | 310.0 | 302.0 | 460 | ✅ Safe |
| **5C — baseline (0.01 m/s)** | **353.8** | **339.6** | 32 | ❌ Unacceptable |
| **5C — optimised (0.4 m/s)** | **317.2** | **304.3** | **1957** | ✅ Safe |

### Velocity Sweep (5C, Python-automated — 10 simulations)

| Velocity (m/s) | T_max (K) | ΔP (Pa) | Pumping Power (mW) |
|----------------|-----------|---------|-------------------|
| 0.01 | 353.8 | 32 | 0.02 |
| 0.05 | 323.5 | 171.6 | 0.43 |
| 0.20 | 318.4 | 897.3 | 8.97 |
| **0.40 ← optimal** | **317.4** | **2360** | **47.2** |
| 1.00 | 316.6 | 10206 | 510.3 |

> **Saturation point:** Beyond 0.4 m/s, T_max decreases by only 0.8 K while pumping power increases 10×.

---

## 🔩 Geometry Optimisation — Channel Width Sweep

Python-automated sweep at **constant mass flow rate** (4.0 → 4.5 mm, 5 simulations):

| Width (mm) | ΔP (Pa) | ΔP Reduction | T_max (K) | T_avg change |
|------------|---------|-------------|-----------|-------------|
| 4.0 (baseline) | 2560 | — | 317.30 | — |
| 4.1 | 2354 | −8.1% | 317.23 | < 0.1 K |
| 4.2 | 2248 | −12.2% | 317.22 | < 0.1 K |
| 4.3 | 2140 | −16.4% | 317.21 | < 0.1 K |
| 4.4 | 2055 | −19.7% | 317.19 | < 0.2 K |
| **4.5 ✅ FINAL** | **1957** | **−23.6%** | **317.16** | < 0.4 K |

> **23.6% hydraulic improvement with only 0.14 K thermal change** — structural limit of plate thickness (1.5 mm base wall) reached at 4.5 mm.

---

## 🧪 Coolant Comparison

| Criterion | Pure Water | 50/50 EG–Water ✅ | Al₂O₃ Nanofluid |
|-----------|-----------|-----------------|----------------|
| Optimal velocity | 0.2 m/s | 0.4 m/s | 0.2 m/s |
| Pumping power | 17.8 mW | 188.9 mW | 19.7 mW |
| Corrosion risk | Moderate | **Lowest (inhibited)** | High (abrasion) |
| Freeze point | 0 °C ❌ | **−37 °C ✅** | ~0 °C ❌ |
| Cost | ~$0.20/L | ~$2.25/L | ~$60.00/L ❌ |
| **Recommendation** | Lab only | **Commercial EV ✅** | R&D only |

---

## ✅ Safety Standards Compliance

| Standard | Requirement | Result | Status |
|----------|-------------|--------|--------|
| IEC 62660 | T_max < 45 °C (318.15 K) | 317.2 K | ✅ PASS |
| ISO 6469 | ΔT_cell ≤ 5 K | ~5 K | ✅ PASS |
| SAE J2464 | No hotspot formation | All cells in range | ✅ PASS |
| Engineering practice | ΔP < 3 kPa | 1957 Pa | ✅ PASS |

---

## 📚 Validation

Results benchmarked against peer-reviewed literature:

| Reference | Aspect | Outcome |
|-----------|--------|---------|
| Panchal et al., *Energies* 2023 | T_max vs. velocity trend | Exponential decay + saturation matched; deviation < 3 K |
| Zhang et al., *ACS Omega* 2022 | ΔP vs. velocity | Near-perfect quadratic correlation |
| Sheng et al., *IJHMT* 2019 | Width sweep ΔP slope | Consistent slope; higher absolute ΔP justified by EG viscosity |
| Liu et al., *Appl. Therm. Eng.* 2022 | Thermal saturation point | Plateau beyond 0.4 m/s confirmed |

---

## 📁 Repository Structure

```
├── cad/
│   └── battery_pack.sldprt          # SolidWorks assembly
├── cfd/
│   ├── mesh/                        # Fluent meshing journal files
│   └── case/                        # Fluent case and data files
├── python/
│   ├── automation_pipeline.py       # Main sweep controller
│   ├── solidworks_api.py            # SolidWorks geometry modifier
│   ├── spaceclaim_api.py            # Named selection re-assignment
│   ├── pyfluent_solver.py           # Solver execution + extraction
│   └── results_parser.py           # Post-processing and plotting
├── results/
│   ├── velocity_sweep/              # T_max, ΔP vs. velocity data
│   ├── width_sweep/                 # T_max, ΔP vs. channel width data
│   └── contours/                    # Temperature contour images
├── report/
│   └── BTMS_Project_Report.docx    # Full technical report
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
```bash
# Python packages
pip install ansys-fluent-core matplotlib numpy pandas

# ANSYS Fluent (licensed installation required)
# SolidWorks (licensed installation required)
```

### Running the velocity sweep
```python
from python.automation_pipeline import VelocitySweep

sweep = VelocitySweep(
    case_path="cfd/case/btms_5C.cas.h5",
    velocities=[0.01, 0.02, 0.03, 0.04, 0.05, 0.125, 0.20, 0.40, 0.60, 0.80, 1.00],
    coolant="water_glycol_50_50",
    output_dir="results/velocity_sweep/"
)
sweep.run()
```

### Running the width sweep
```python
from python.automation_pipeline import WidthSweep

sweep = WidthSweep(
    sldprt_path="cad/battery_pack.sldprt",
    widths=[4.0, 4.1, 4.2, 4.3, 4.4, 4.5],
    mass_flow_rate=0.0212,   # kg/s — constant across all variants
    output_dir="results/width_sweep/"
)
sweep.run()
```

---

## 👤 Author

**Emirhan Karagöz**
Trakya University — Faculty of Engineering
Student ID: 2201601024
2024–2025

---

## 📄 License

This project was developed as a graduation project at Trakya University. Academic use permitted with attribution.
