# Fire Spread Calibration Guide

This document details the empirical calibration parameters used by the Cellular Automata (CA) fire spread engine for 500m x 500m spatial grids.

## 1. Cellular Automata Model Overview

The MVP fire spread simulation uses an 8-neighbour Moore neighbourhood Cellular Automata framework:
- State $S \in \{\text{UNBURNED}, \text{BURNING}, \text{BURNED}, \text{NON\_BURNABLE}\}$
- Grid resolution: $500\text{ m} \times 500\text{ m}$ ($25\text{ ha}$ per cell)
- Propagation timesteps: Hourly snapshots with internal discrete sub-steps ($\Delta t = 30\text{ minutes}$, 2 sub-steps per hour).

## 2. Parameter Reference

| Parameter | Default Value | Physical / Empirical Basis |
| :--- | :--- | :--- |
| `base_spread_probability` | `0.28` | Baseline unassisted fire advance rate on flat calm terrain (~0.35–0.50 km/h). |
| `wind_coefficient` | `0.15` | Matches forward flame tilt and convective heat transfer at winds up to 25 m/s. |
| `backing_coefficient` | `0.10` | Governs backing fire retardation when spreading against opposing wind airflow. |
| `slope_uphill_coeff` | `2.0` | Exponential spread acceleration on uphill gradients ($\tan(\phi)$ scaling up to 45°). |
| `slope_downhill_coeff` | `1.0` | Retardation when flame tilts away from unburned downhill fuels. |
| `solar_aspect_coeff` | `0.20` | Insolation modulation for Western Himalayas (peak solar drying on south-facing slopes ~180°). |
| `burning_duration_steps` | `3` | Represents fuel residence time before flaming exhaustion (approx. 1.5 hours on 25 ha cell). |
| `spread_threshold` | `0.25` | Deterministic ignition cutoff threshold ensuring repeatable simulation behavior. |

## 3. Comparison: CA Empirical Parameters vs. Rothermel Physics (Phase 10+)

| Dimension | MVP Cellular Automata (Phase 7) | Rothermel Physics Model (Phase 10+) |
| :--- | :--- | :--- |
| **Foundation** | Empirical directional probability multipliers ($K_w, K_s, K_a, K_f$) | Semi-physical heat balance differential equations ($I_R \cdot \xi / (\rho_b \cdot \epsilon \cdot Q_{ig})$) |
| **Wind Coupling** | Directional cosine with exponential velocity scaling | Midflame wind factor $\phi_w = C \cdot U^B \cdot (\beta / \beta_{op})^{-E}$ |
| **Topography** | Projected slope tangent and solar azimuth correction | Slope factor $\phi_s = 5.275 \cdot \beta^{-0.3} \cdot (\tan \phi)^2$ |
| **Fuel Model** | Canonical categorical flammability factors ($0.0$ to $1.8$) | Fuel bed bulk density, fuel loading by size class (1h, 10h, 100h), surface-area-to-volume ratio ($S_v$), heat content ($h$), moisture of extinction ($M_x$) |
| **Runtime Cost** | Ultra-fast ($< 100\text{ ms}$ for 12 hours on 50x50 grid) | Moderate to high (numerical ODE integration per cell/wavefront) |
| **Scope** | Operational rapid tactical assessment | Detailed scientific and physical fire behavior forecasting |
