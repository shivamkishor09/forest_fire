"""Canadian Fire Weather Index (FWI) System calculation and documented interface."""

import math
from typing import Dict, Optional


class FwiCalculator:
    """
    Standard Canadian Forest Fire Weather Index (FWI) calculation engine.
    Calculates FFMC, DMC, DC, ISI, BUI, and overall FWI from daily noon/peak meteorological observations.
    """

    # Effective day lengths for DMC (approx. 20°N - 35°N sub-tropical Indian latitudes)
    DAY_LENGTH_DMC = [6.5, 7.5, 9.0, 12.8, 13.9, 13.9, 12.4, 10.9, 9.4, 8.0, 7.0, 6.0]

    # Day length adjustment factors for DC
    DRYING_FACTOR_DC = [-1.6, -1.6, -1.6, 0.9, 3.8, 5.8, 6.4, 5.0, 2.4, 0.4, -1.6, -1.6]

    @classmethod
    def compute_ffmc(
        cls,
        temperature_c: float,
        rh_pct: float,
        wind_kmh: float,
        rain_mm: float,
        prev_ffmc: float = 85.0,
    ) -> float:
        """
        Compute Fine Fuel Moisture Code (FFMC) representing top litter layer (1.2 cm) moisture.
        Scale: 0-101. High values (>85) indicate rapid ignition potential.
        """
        temp = temperature_c
        rh = min(max(rh_pct, 1.0), 100.0)
        wind = max(wind_kmh, 0.0)
        rain = max(rain_mm, 0.0)

        # Previous equilibrium moisture content
        m_prev = 147.2 * (101.0 - prev_ffmc) / (59.5 + prev_ffmc)

        # Rain effect
        if rain > 0.5:
            r_eff = rain - 0.5
            if m_prev > 150.0:
                mr = m_prev + 42.5 * r_eff * math.exp(-100.0 / (251.0 - m_prev)) * (1.0 - math.exp(-6.93 / r_eff))
            else:
                mr = m_prev + 42.5 * r_eff * math.exp(-100.0 / (251.0 - m_prev)) * (1.0 - math.exp(-6.93 / r_eff)) + 0.0015 * (m_prev - 150.0) ** 2 * math.sqrt(r_eff)
            mr = min(mr, 250.0)
        else:
            mr = m_prev

        # Equilibrium moisture content for drying / wetting
        ed = 0.942 * (rh ** 0.679) + (11.0 * math.exp((rh - 100.0) / 10.0)) + 0.18 * (21.1 - temp) * (1.0 - math.exp(-0.115 * rh))
        ew = 0.618 * (rh ** 0.753) + (10.0 * math.exp((rh - 100.0) / 10.0)) + 0.18 * (21.1 - temp) * (1.0 - math.exp(-0.115 * rh))

        if mr < ed:
            # Wetting phase
            k1 = 0.424 * (1.0 - ((100.0 - rh) / 100.0) ** 1.7) + (0.0694 * math.sqrt(wind)) * (1.0 - ((100.0 - rh) / 100.0) ** 8)
            kw = k1 * 0.581 * math.exp(0.0365 * temp)
            m = ew + (mr - ew) * (10.0 ** (-kw))
        elif mr > ed:
            # Drying phase
            k0 = 0.424 * (1.0 - (rh / 100.0) ** 1.7) + (0.0694 * math.sqrt(wind)) * (1.0 - (rh / 100.0) ** 8)
            kd = k0 * 0.581 * math.exp(0.0365 * temp)
            m = ed + (mr - ed) * (10.0 ** (-kd))
        else:
            m = mr

        ffmc = (59.5 * (250.0 - m)) / (147.2 + m)
        return round(min(max(ffmc, 0.0), 101.0), 2)

    @classmethod
    def compute_isi(cls, wind_kmh: float, ffmc: float) -> float:
        """
        Compute Initial Spread Index (ISI) from wind speed and FFMC.
        Represents relative rate of fire spread without fuel buildup factor.
        """
        wind = max(wind_kmh, 0.0)
        f_wind = math.exp(0.05039 * wind)
        m = 147.2 * (101.0 - ffmc) / (59.5 + ffmc)
        f_ffmc = 91.9 * math.exp(-0.1386 * m) * (1.0 + (m ** 5.31) / (4.93e7))
        isi = 0.208 * f_wind * f_ffmc
        return round(max(isi, 0.0), 2)

    @classmethod
    def compute_dmc(
        cls,
        temperature_c: float,
        rh_pct: float,
        rain_mm: float,
        prev_dmc: float = 6.0,
        month: int = 5,
    ) -> float:
        """Compute Duff Moisture Code (DMC) for intermediate organic layer (~7cm)."""
        temp = max(temperature_c, -1.1)
        rh = min(max(rh_pct, 1.0), 100.0)
        rain = max(rain_mm, 0.0)

        # Rain effect
        if rain > 1.5:
            re = 0.92 * rain - 1.27
            mo = 20.0 + math.exp(5.6348 - prev_dmc / 43.43)
            if prev_dmc <= 33.0:
                b = 100.0 / (0.5 + 0.3 * prev_dmc)
            elif prev_dmc <= 65.0:
                b = 14.0 - 1.3 * math.log(prev_dmc)
            else:
                b = 6.2 * math.log(prev_dmc) - 17.2
            mr = mo + 1000.0 * re / (48.77 + b * re)
            pr = max(244.72 - 43.43 * math.log(mr - 20.0), 0.0)
        else:
            pr = prev_dmc

        # Drying factor
        m_idx = min(max(month - 1, 0), 11)
        eff_day_len = cls.DAY_LENGTH_DMC[m_idx]
        k = 1.894 * (temp + 1.1) * (100.0 - rh) * eff_day_len * 1e-4
        dmc = pr + 100.0 * k
        return round(max(dmc, 0.0), 2)

    @classmethod
    def compute_dc(
        cls,
        temperature_c: float,
        rain_mm: float,
        prev_dc: float = 15.0,
        month: int = 5,
    ) -> float:
        """Compute Drought Code (DC) for deep compact organic layers (~18cm)."""
        temp = max(temperature_c, -2.8)
        rain = max(rain_mm, 0.0)

        if rain > 2.8:
            rd = 0.83 * rain - 1.27
            qo = 800.0 * math.exp(-prev_dc / 400.0)
            qr = qo + 3.937 * rd
            dr = max(400.0 * math.log(800.0 / qr), 0.0)
        else:
            dr = prev_dc

        m_idx = min(max(month - 1, 0), 11)
        lf = cls.DRYING_FACTOR_DC[m_idx]
        v = max(0.36 * (temp + 2.8) + lf, 0.0)
        dc = dr + 0.5 * v
        return round(max(dc, 0.0), 2)

    @classmethod
    def compute_bui(cls, dmc: float, dc: float) -> float:
        """Compute Buildup Index (BUI) combining DMC and DC."""
        if dmc <= 0.4 * dc:
            bui = (0.8 * dmc * dc) / (dmc + 0.4 * dc)
        else:
            bui = dmc - (1.0 - 0.8 * dc / (dmc + 0.4 * dc)) * (0.92 + (0.0114 * dmc) ** 1.7)
        return round(max(bui, 0.0), 2)

    @classmethod
    def compute_fwi(cls, isi: float, bui: float) -> float:
        """
        Compute Fire Weather Index (FWI) composite intensity rating from ISI and BUI.
        """
        if bui <= 80.0:
            fd = 0.626 * (bui ** 0.809) + 2.0
        else:
            fd = 1000.0 / (25.0 + 108.64 * math.exp(-0.023 * bui))
        b = 0.1 * isi * fd
        if b > 1.0:
            fwi = math.exp(2.72 + 0.434 * math.log(b))
        else:
            fwi = b
        return round(max(fwi, 0.0), 2)

    @classmethod
    def calculate_all_indices(
        cls,
        temperature_c: float,
        rh_pct: float,
        wind_speed_ms: float,
        precipitation_24h_mm: float = 0.0,
        month: int = 5,
        prev_ffmc: float = 85.0,
        prev_dmc: float = 6.0,
        prev_dc: float = 15.0,
    ) -> Dict[str, float]:
        """
        Compute complete suite of Canadian FWI components from standard input metrics.
        """
        wind_kmh = wind_speed_ms * 3.6
        ffmc = cls.compute_ffmc(temperature_c, rh_pct, wind_kmh, precipitation_24h_mm, prev_ffmc)
        isi = cls.compute_isi(wind_kmh, ffmc)
        dmc = cls.compute_dmc(temperature_c, rh_pct, precipitation_24h_mm, prev_dmc, month)
        dc = cls.compute_dc(temperature_c, precipitation_24h_mm, prev_dc, month)
        bui = cls.compute_bui(dmc, dc)
        fwi = cls.compute_fwi(isi, bui)

        return {
            "ffmc": ffmc,
            "isi": isi,
            "dmc": dmc,
            "dc": dc,
            "bui": bui,
            "fwi": fwi,
        }
