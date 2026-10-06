# 12-Hour Fire Spread Simulation Engine

The **Spread Engine** (`services/spread-engine`) simulates the hourly propagation of wildland forest fires across a standardized 500m x 500m spatial grid for up to 12 hours. It implements a physics-informed Cellular Automata (CA) framework tuned for Western Himalayan and Indian forest ecosystems.

---

## 1. Core Architecture

The Cellular Automata model represents the landscape as a 2D discrete spatial grid:
```
Spatial Grid (500m × 500m cells)
  ├── State Matrix:        [UNBURNED = 0, BURNING = 1, BURNED = 2, NON_BURNABLE = 3]
  ├── Burn Timer Matrix:   Sub-step countdown before flaming exhaustion to BURNED
  ├── Elevation Raster:    DEM surface elevation (meters)
  ├── Slope Raster:        Topographic inclination (degrees, 0° to 90°)
  ├── Aspect Raster:       Downhill azimuth bearing (degrees, 0° to 360°)
  └── Fuel Raster:         Categorical Indian forest fuel flammability classes
```

### Discrete Cell States
- `UNBURNED (0)`: Combustible fuel bed available for ignition.
- `BURNING (1)`: Actively combusting cell generating convective and radiative heat to 8 neighbours.
- `BURNED (2)`: Exhausted fuel bed; inactive, cannot re-ignite.
- `NON_BURNABLE (3)`: Water bodies, rivers, rock outcrops, snow; zero combustibility.

---

## 2. 8-Neighbour Moore Neighbourhood

Propagation from a burning cell $(r, c)$ evaluates all 8 adjacent cells:
```
      NW (-1,-1, 315°)     N (-1,0, 0°)     NE (-1,1, 45°)
      W  (0,-1, 270°)      ● BURNING (r,c)   E  (0,1, 90°)
      SW (1,-1, 225°)      S (1,0, 180°)    SE (1,1, 135°)
```
- **Orthogonal neighbors** (N, E, S, W): Distance $d = 500\text{ m}$, distance weight $W = 1.0$.
- **Diagonal neighbors** (NE, SE, SW, NW): Distance $d = 500\sqrt{2} \approx 707.1\text{ m}$, distance weight $W = 1/\sqrt{2} \approx 0.7071$.

---

## 3. Environmental Spread Factors

The ignition probability from burning cell $i$ to candidate unburned cell $j$ along propagation heading $\theta_{\text{prop}}$ is:
$$P_{i \to j} = P_{\text{base}} \times K_w \times K_s \times K_a \times K_f \times W_{\text{dist}}$$

### 3.1 Directional Wind Factor ($K_w$)
Meteorological wind direction $\theta_{\text{met}}$ denotes the direction **from** which wind blows. Fire pushes downwind towards $\theta_{\text{blow}} = (\theta_{\text{met}} + 180^\circ) \bmod 360^\circ$.
$$\Delta \theta = ((\theta_{\text{prop}} - \theta_{\text{blow}} + 180^\circ) \bmod 360^\circ) - 180^\circ$$
- **Downwind / Lateral** ($\cos \Delta \theta \ge 0$):
  $$K_w = 1.0 + c_w \cdot U^{1.1} \cdot \cos(\Delta \theta)$$
- **Backing Fire** ($\cos \Delta \theta < 0$):
  $$K_w = \frac{1.0}{1.0 + c_{\text{back}} \cdot U \cdot |\cos(\Delta \theta)|}$$

### 3.2 Topographic Slope Factor ($K_s$)
Terrain slope accelerates uphill spread and retards downhill spread:
$$\phi_{\text{eff}} = \text{slope} \cdot \cos(\theta_{\text{prop}} - \text{uphill\_bearing})$$
- **Uphill** ($\phi \ge 0$): $K_s = \exp(c_s \cdot \tan \phi)$
- **Downhill** ($\phi < 0$): $K_s = \exp(-c_{\text{down}} \cdot |\tan \phi|)$

### 3.3 Solar Insolation Aspect Factor ($K_a$)
In the Northern Hemisphere (~30°N), south-facing slopes (azimuth 180°) receive peak midday solar drying:
$$K_a = 1.0 + c_a \cdot \sin(\min(\text{slope}, 45^\circ)) \cdot \cos(\text{aspect} - 180^\circ)$$

### 3.4 Fuel Bed Combustibility ($K_f$)
Calibrated against Indian forest inventory types:
- `CONIFER_HIGH_FLAMMABILITY` (*Chir Pine*): $1.80$
- `GRASSLAND_FAST_SPREAD` (*Scrub / Grassland*): $1.50$
- `CONIFER_MODERATE_FLAMMABILITY` (*Deodar / Fir / Spruce*): $1.30$
- `BROADLEAF_HIGH_LITTER` (*Sal Deciduous*): $1.20$
- `BROADLEAF_MODERATE_LITTER` (*Dry Deciduous*): $1.00$ (reference)
- `SHRUB_COMPACT` (*Heath*): $0.90$
- `AGRICULTURE_SEASONAL` (*Cropland*): $0.60$
- `NON_BURNABLE_WATER` / `NON_BURNABLE_BARREN`: $0.00$ (firebreaks)

---

## 4. Multi-Neighbor Ignition & Double Buffering

When cell $j$ borders multiple active burning cells $\{i_1, i_2, \dots\}$:
$$P_{\text{ignite}}(j) = 1 - \prod_{k} (1 - P_{i_k \to j})$$
- **Deterministic Mode**: Cell ignites if $P_{\text{ignite}} \ge P_{\text{threshold}}$.
- **Stochastic Mode**: Cell ignites if $U(0, 1) < P_{\text{ignite}}$ (seeded pseudorandom generator).
- **Double Buffering**: State transitions are evaluated against current grid arrays and simultaneously committed into next buffer to ensure strict step-wise order independence.

---

## 5. Geometric Boundary Extraction (GeoJSON)

At each hourly snapshot:
1. All actively `BURNING` and `BURNED` cells are transformed into WGS 84 bounding boxes.
2. `shapely.unary_union` dissolves shared interior cell edges.
3. Clean polygon boundaries are simplified and formatted into RFC 7946 compliant GeoJSON Polygons / MultiPolygons.

---

## 6. Simulation Output Metrics

For each hour $T \in [1, 12]$:
- `step_hour`: Simulation hour (1-12).
- `burned_area_ha`: Cumulative area burned in hectares ($25\text{ ha} \times \text{cell\_count}$).
- `spread_velocity_kmh`: Maximum fire front propagation speed from ignition center ($\text{km/h}$).
- `spread_direction_deg`: Compass heading of fire centroid expansion vector (degrees).
- `intensity_mw`: Estimated radiative fire power based on active flaming perimeter and wind speed.
- `boundary_polygon`: GeoJSON boundary polygon.

---

## 7. Standalone CLI Usage

Run a simulation directly from the terminal without external services:

```bash
# 6-hour simulation with 7.5 m/s wind from South
python -m services.spread_engine.cli \
  --lat 30.2 \
  --lon 78.7 \
  --duration 6 \
  --wind-speed 7.5 \
  --wind-dir 180.0 \
  --fuel CONIFER_HIGH_FLAMMABILITY \
  --output ./sim_output.geojson
```

---

## 8. Python Programmatic API

```python
from services.spread_engine.models.config import SimulationInput, EnvironmentalConditions
from services.spread_engine.simulation.runner import CellularAutomataRunner

runner = CellularAutomataRunner()
sim_input = SimulationInput(
    simulation_id="sim-run-demo",
    ignition_lat=30.22,
    ignition_lon=78.78,
    duration_hours=12,
    environment=EnvironmentalConditions(wind_speed_ms=8.0, wind_direction_deg=225.0),
    fuel_type="CONIFER_HIGH_FLAMMABILITY",
)

result = runner.run_simulation(sim_input)
print(f"Total Burned: {result.total_area_burned_ha} ha")
print(f"Peak Velocity: {result.peak_spread_velocity_kmh} km/h")

# Serialize to GeoJSON FeatureCollection
geojson_data = result.to_geojson()
```
