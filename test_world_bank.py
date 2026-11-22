"""Which World Bank indicators to pull, and from which API source.

Each entry maps a short, readable name (used everywhere downstream)
to the official indicator code and the World Bank API source id.
Source 2 = World Development Indicators (WDI), 3 = Worldwide Governance Indicators (WGI).
"""

INDICATORS = {
    # --- Economy & poverty ---
    "gdp_per_capita_ppp": {"code": "NY.GDP.PCAP.PP.KD", "source": 2},  # constant intl $
    "poverty_rate": {"code": "SI.POV.DDAY", "source": 2},  # % below international poverty line
    "inflation_cpi": {"code": "FP.CPI.TOTL.ZG", "source": 2},  # annual %
    # --- Population & geography ---
    "rural_share": {"code": "SP.RUR.TOTL.ZS", "source": 2},  # % of population
    "population_density": {"code": "EN.POP.DNST", "source": 2},  # people per km2
    # --- Human capital ---
    "adult_literacy": {"code": "SE.ADT.LITR.ZS", "source": 2},  # % of people 15+
    # --- Finance ---
    "account_ownership": {"code": "FX.OWN.TOTL.ZS", "source": 2},  # % of people 15+ (Findex)
    # --- Governance ---
    "gov_effectiveness": {"code": "GE.EST", "source": 3},  # WGI estimate, about -2.5 to 2.5
    "control_of_corruption": {"code": "CC.EST", "source": 3},  # WGI estimate
}

# Cash transfer RCTs start in the late 1990s; keep some margin before that.
START_YEAR = 1990
END_YEAR = 2025

API_BASE = "https://api.worldbank.org/v2"
