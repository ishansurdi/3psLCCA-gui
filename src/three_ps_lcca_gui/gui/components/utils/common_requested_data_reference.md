# `common_requested_data` — Function Reference

> Schemas shown for chunks where docstrings are available.

---

## Generic

### `get_chunk(chunk_name) -> dict`
Return a chunk dict via the controller cache. Uses `controller.get_chunk()` — not `engine.fetch_chunk()` — so staged-but-not-yet-flushed saves are included.

### `get_all_data() -> dict`
Return all known chunks as a flat dict keyed by chunk name.

---

## general_info

### `get_general_info() -> dict`
Return the general info chunk.

### `get_currency() -> str`
Return the project currency string, or `'Currency'` if unavailable.

### `get_project_country() -> str`
Return the project country string.

### `get_project_name() -> str`
Return the project name string.

---

## bridge_data

### `get_bridge_data() -> dict`

```
{
    "bridge_name":                  str,    # e.g. "Mumbai Project"
    "user_agency":                  str,
    "project_country":              str,
    "location":                     str,
    "bridge_type":                  str,    # e.g. "Girder"
    "span":                         float,
    "carriageway_width":            float,
    "num_lanes":                    int,
    "vehicle_path_direction":       str,    # e.g. "One Way"
    "footpath":                     str,    # e.g. "No footpath"
    "design_life":                  int,    # e.g. 75
    "analysis_period":              int,    # e.g. 100
    "year_of_construction":         int,    # e.g. 2026
    "duration_construction_months": float,  # e.g. 5.2
    "working_days_per_month":       int,    # e.g. 22
    "days_per_month":               int,    # e.g. 30
}
```

### `get_design_life() -> int | None`
Returns `bridge_data["design_life"]`.

### `get_analysis_period() -> int | None`
Returns `analysis_period["analysis_period"]`.

### `get_construction_duration_months() -> float | None`
Returns `bridge_data["duration_construction_months"]`.

---

## financial_data

### `get_financial_data() -> dict`

```
{
    "discount_rate":           float,  # e.g. 6.7
    "discount_rate_source":    str,
    "inflation_rate":          float,  # e.g. 5.15
    "inflation_rate_source":   str,
    "interest_rate":           float,  # e.g. 7.75
    "interest_rate_source":    str,
    "investment_ratio":        float,  # e.g. 0.5
    "investment_ratio_source": str,
}
```

### `get_discount_rate() -> float | None`
Returns `financial_data["discount_rate"]`.

---

## maintenance_data

### `get_maintenance_data() -> dict`

```
{
    "routine_inspection_cost":          float,  # % of construction cost, e.g. 0.1
    "routine_inspection_freq":          int,    # years, e.g. 1
    "periodic_maintenance_cost":        float,  # % of construction cost, e.g. 0.6
    "periodic_maintenance_carbon_cost": float,  # % of construction carbon cost, e.g. 0.55
    "periodic_maintenance_freq":        int,    # years, e.g. 5
    "major_inspection_cost":            float,  # % of construction cost, e.g. 0.5
    "major_inspection_freq":            int,    # years, e.g. 5
    "major_repair_cost":                float,  # % of construction cost, e.g. 10.0
    "major_repair_carbon_cost":         float,  # % of construction carbon cost, e.g. 0.55
    "major_repair_freq":                int,    # years, e.g. 60
    "major_repair_duration":            int,    # months, e.g. 3
    "bearing_exp_joint_cost":           float,  # % of construction cost, e.g. 12.5
    "bearing_exp_joint_freq":           int,    # years, e.g. 25
    "bearing_exp_joint_duration":       int,    # months, e.g. 2
}
```

---

## demolition_data

### `get_demolition_data() -> dict`

```
{
    "demolition_cost_pct":        float,  # e.g. 10.0
    "demolition_carbon_cost_pct": float,  # e.g. 10.0
    "demolition_duration":        int,    # months, e.g. 1
}
```

---

## traffic_and_road_data

### `get_traffic_and_road_data() -> dict`
Schema not yet documented.

---

## Structural (foundation / sub-structure / super-structure / misc)

All four return the same shape — component names as keys, each value a list of work items.

### `get_str_foundation() -> dict`
Component names e.g. `"Excavation"`, `"Pile"`, `"Pile Cap"`.

### `get_str_sub_structure() -> dict`
Component names e.g. `"Abutment"`, `"Pier"`.

### `get_str_super_structure() -> dict`
Component names e.g. `"Girder"`, `"Deck Slab"`.

### `get_str_misc() -> dict`
Component names e.g. `"Railing"`, `"Wearing Coat"`.

**Shared work item schema:**

```
{
    "<ComponentName>": [
        {
            "id": str,              # UUID
            "values": {
                "src_id":                              str | None,   # e.g. "12.01"
                "material_name":                       str,
                "quantity":                            float,
                "unit":                                str,          # e.g. "m3", "m"
                "unit_to_si":                          float,        # multiplier → SI base unit
                "rate":                                float,        # cost per unit
                "rate_source":                         str | None,   # e.g. "Bihar SOR"
                "carbon_emission":                     float | None, # embodied carbon factor
                "carbon_unit":                         str | None,   # e.g. "kgCO₂e/kg"
                "carbon_emission_src":                 str | None,   # e.g. "IFC"
                "conversion_factor":                   float | None, # density kg/m³, e.g. 2400
                "scrap_rate":                          float | None, # % scrapped during construction
                "post_demolition_recovery_percentage": float | None, # 0–100
                "transport_kg_factor":                 float | None, # kg/m³ for transport calcs
            },
            "meta": {
                "created_on":    str,   # ISO 8601 datetime
                "modified_on":   str,   # ISO 8601 datetime
                "source":        str,   # "manual" | "db" | "excel" | "db_modified" | "excel_modified"
                "source_db_key": str,   # e.g. "INDIA/Bihar/Darbhanga-2025"; "" if not from DB
                "db_original":   dict,  # snapshot of the record as ingested
            },
            "state": {
                "in_trash":                   bool,        # soft-deleted
                "included_in_carbon_emission": bool | None, # None = not yet decided
                "included_in_recyclability":   bool,
                "allow_edit_checked":          bool,
                "carbon_conversion_confirmed": bool,
            },
        },
        # ... more work items
    ],
    # ... more component groups
}
```

---

## transport_data

### `get_transport_data() -> dict`
Schema not yet documented.

---

## machinery_emissions_data

### `get_machinery_emissions_data() -> dict`

**Mode: `"detailed"`**
```
{
    "mode":         str,    # "detailed"
    "default_days": int,
    "detailed": {
        "rows": [
            {
                "name":   str,    # e.g. "Backhoe loader (JCB)"
                "source": str,    # "Diesel" | "Electricity (Grid)"
                "rate":   float,  # fuel/energy consumption rate
                "hrs":    float,  # hours per day
                "days":   int,    # number of days used
                "ef":     float,  # emission factor kgCO2e — 2.69 Diesel, 0.71 Grid
            },
            # ... more rows
        ]
    },
    "lumpsum":      dict,   # present but unused in this mode
    "remarks":      str,    # HTML-formatted rich text
    "total_kgCO2e": float,
}
```

**Mode: `"lumpsum"`**
```
{
    "mode":         str,    # "lumpsum"
    "default_days": int,
    "detailed":     dict,   # present but unused in this mode
    "lumpsum": {
        "elec_consumption_per_day": float,  # kWh/day
        "elec_days":                int,
        "elec_ef":                  float,  # emission factor for electricity
        "fuel_consumption_per_day": float,  # litres/day
        "fuel_days":                int,
    },
    "remarks":      str,    # HTML-formatted rich text
    "total_kgCO2e": float,
}
```

---

## social_cost_data

### `get_social_cost_data() -> dict`

```
{
    "source": "K. Ricke et al. (Country-Level)",
    "ricke": {
        "iso3": "AFG",
        "ssp": "SSP1 (Sustainability)",
        "rcp": "Closest RCP (Default)",
        "dmg_func": "BHM SR (Short Run)",
        "dmg_params": "Bootstrap (Full Uncertainty)",
        "climate_uncertainty": "Expected (Central Projections)",
        "discounting": "Growth-adjusted (prtp=1%, η=1.5)",
        "percentile": "50.0% (Central)",
        "usd_to_local_rate": 95.0,
        "cpi_ratio": 1.0
    },
    "custom": {
        "entered_value": 0.0,
        "currency": "INR",
        "unit": "INR/kgCO₂e"
    },
    "result": {
        "selected_mode": "K. Ricke et al. (Country-Level)",
        "cost_of_carbon_local": 4.469941721470338,
        "currency": "INR",
        "unit": "INR/kgCO₂e"
    }
}
```

### `get_social_cost_mode() -> str`
Returns `social_cost_data["mode"]`.

### `get_social_cost() -> float | None`
Returns `social_cost_data["cost"]`.

### `get_social_cost_ricke() -> dict`
Returns `social_cost_data["ricke"]`.

### `get_social_cost_usd_to_local_rate() -> float | None`
Returns `social_cost_data["ricke"]["usd_to_local_rate"]`.

### `get_social_cost_cpi_ratio() -> float | None`
Returns `social_cost_data["ricke"]["cpi_ratio"]`.

### `get_social_cost_custom_scc_value() -> float | None`
Returns `social_cost_data["custom"]["scc_value"]`.

---

## diversion_emissions

### `get_diversion_emissions_data() -> dict`

**Mode: `"Calculate by Vehicle"`**
```
{
    "mode": str,    # "Calculate by Vehicle"
    "emission_factors": {
        "small_cars":   float,  # e.g. 0.103
        "big_cars":     float,  # e.g. 0.269
        "two_wheelers": float,  # e.g. 0.035
        "o_buses":      float,  # e.g. 0.455
        "d_buses":      float,  # e.g. 0.606
        "lcv":          float,  # e.g. 0.307
        "hcv":          float,  # e.g. 0.593
        "mcv":          float,  # e.g. 0.738
    },
    "total_calculated_emissions": float,  # e.g. 578.49
    "remarks":                    str,    # HTML-formatted rich text
}
```

**Mode: `"Enter Directly"`**
```
{
    "mode":                   str,    # "Enter Directly"
    "total_direct_emissions": float,  # e.g. 1000.0
    "remarks":                str,    # HTML-formatted rich text
}
```

### `get_diversion_emissions_cost() -> tuple[str, float | None]`
Returns `(mode, cost)` resolved from the active mode:
- `"Calculate by Vehicle"` → `total_calculated_emissions`
- `"Enter Directly"` → `total_direct_emissions`
- Unrecognised mode → `("", None)`

---

## str_summary

### `get_str_summary() -> dict`

```
{
    "foundation":      {"total": float, "items": int, "components": int},
    "substructure":    {"total": float, "items": int, "components": int},
    "super_structure": {"total": float, "items": int, "components": int},
    "misc":            {"total": float, "items": int, "components": int},
    "grand_total":     float,
    "total_items":     int,
}
```

### `get_str_summary_grand_total() -> float | None`
Returns `str_summary["grand_total"]`.
