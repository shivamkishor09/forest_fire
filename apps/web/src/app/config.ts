/**
 * Application-wide configuration and environmental constants
 */

export const APP_CONFIG = {
  // API URL
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',

  // Tile layers
  tileLayers: {
    darkMatter: {
      url: import.meta.env.VITE_MAPBOX_ACCESS_TOKEN
        ? `https://api.mapbox.com/styles/v1/mapbox/dark-v11/tiles/256/{z}/{x}/{y}?access_token=${import.meta.env.VITE_MAPBOX_ACCESS_TOKEN}`
        : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: import.meta.env.VITE_MAPBOX_ACCESS_TOKEN
        ? '&copy; <a href="https://www.mapbox.com/about/maps/">Mapbox</a> &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    },
    osm: {
      url: import.meta.env.VITE_MAPBOX_ACCESS_TOKEN
        ? `https://api.mapbox.com/styles/v1/mapbox/outdoors-v12/tiles/256/{z}/{x}/{y}?access_token=${import.meta.env.VITE_MAPBOX_ACCESS_TOKEN}`
        : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    },
    satellite: {
      url: import.meta.env.VITE_MAPBOX_ACCESS_TOKEN
        ? `https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/tiles/256/{z}/{x}/{y}?access_token=${import.meta.env.VITE_MAPBOX_ACCESS_TOKEN}`
        : 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attribution: import.meta.env.VITE_MAPBOX_ACCESS_TOKEN
        ? '&copy; <a href="https://www.mapbox.com/about/maps/">Mapbox</a> &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        : 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
      maxZoom: 19,
    },
  },

  // Default geographic viewport (Uttarakhand / Western Himalayas)
  defaultViewport: {
    lat: 30.2241,
    lng: 78.7842,
    zoom: 9,
  },

  // Standard spatial grid properties
  grid: {
    resolutionMeters: 500,
    areaHectaresPerCell: 25, // 500m * 500m = 250,000m² = 25 ha
    projection: 'EPSG:4326',
  },

  // Simulation bounds
  simulation: {
    minDurationHours: 1,
    maxDurationHours: 12,
    defaultDurationHours: 6,
    defaultStepMinutes: 60,
  },

  // Standard Risk Color System (consistent across all GIS layers and UI)
  riskColors: {
    LOW: {
      label: 'Low',
      fillColor: '#3F7D58', // forest green
      strokeColor: '#2D5E41',
      fillOpacity: 0.45,
      threshold: '0.00 – 0.25',
      badgeBg: 'bg-forest/15 text-forest border-forest/30',
    },
    MODERATE: {
      label: 'Moderate',
      fillColor: '#D99A2B', // warm amber
      strokeColor: '#B07B1E',
      fillOpacity: 0.5,
      threshold: '0.25 – 0.50',
      badgeBg: 'bg-amber/15 text-amber border-amber/30',
    },
    HIGH: {
      label: 'High',
      fillColor: '#E06D2E', // orange
      strokeColor: '#BD571F',
      fillOpacity: 0.6,
      threshold: '0.50 – 0.75',
      badgeBg: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
    },
    EXTREME: {
      label: 'Extreme',
      fillColor: '#D84A3A', // strong red
      strokeColor: '#B33729',
      fillOpacity: 0.7,
      threshold: '0.75 – 1.00',
      badgeBg: 'bg-danger/15 text-danger border-danger/30',
    },
  },
  // Operational Attention & Advisory Levels
  alertLevels: {
    INFO: {
      label: 'Operational Baseline',
      badgeClass: 'bg-ops-surface text-txt-secondary border-ops-border',
    },
    WARNING: {
      label: 'Elevated Activity',
      badgeClass: 'bg-amber/15 text-amber border-amber/40',
    },
    HIGH_ATTENTION: {
      label: 'Critical Fire Danger',
      badgeClass: 'bg-danger/15 text-danger border-danger/40',
    },
  },
} as const;

export type RiskLevelKey = keyof typeof APP_CONFIG.riskColors;
export type AlertLevelKey = keyof typeof APP_CONFIG.alertLevels;

