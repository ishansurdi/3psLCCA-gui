from pathlib import Path

from PySide6.QtWidgets import QPushButton, QHBoxLayout, QWidget, QLabel

from three_ps_lcca_gui.gui.themes import get_token
from ....base_widget import ScrollableForm
from ....utils.form_builder.form_definitions import FieldDef, Section
from ....utils.form_builder.form_builder import build_form, _PLACEHOLDER
from ....utils.display_format import DECIMAL_PLACES
from ....utils.validation_helpers import freeze_form, validate_form, clear_field_styles, confirm_clear_all

# ── DB helpers (mirrors cscc_explorer.py) ─────────────────────────────────────

_PKL_PATH = Path(__file__).parent.parent.parent / "cscc-database-2018-master" / "cscc_db.pkl"

_CLOSEST_RCP = {"SSP1": "rcp60", "SSP2": "rcp60", "SSP3": "rcp85", "SSP4": "rcp60", "SSP5": "rcp85"}

_SSP_LABEL_MAP = {
    "SSP1 (Sustainability)":           "SSP1",
    "SSP2 (Middle of the Road)":       "SSP2",
    "SSP3 (Regional Rivalry)":         "SSP3",
    "SSP4 (Inequality)":               "SSP4",
    "SSP5 (Fossil-fueled Development)": "SSP5",
}

_RCP_LABEL_MAP = {
    "Closest RCP (default)":        None,
    "RCP4.5 (≈ +2.5°C in 2100)":   "rcp45",
    "RCP6.0 (≈ +3°C in 2100)":     "rcp60",
    "RCP8.5 (≈ +4.5°C in 2100)":   "rcp85",
}

_DMG_FUNC_LABEL_MAP = {
    "BHM SR (Short Run)":               "bhm_sr",
    "BHM RP SR (Rich/Poor Short Run)":  "bhm_richpoor_sr",
    "BHM LR (Long Run)":                "bhm_lr",
    "BHM RP LR (Rich/Poor Long Run)":   "bhm_richpoor_lr",
}

_DMG_PARAMS_LABEL_MAP = {
    "bootstrap (full uncertainty)":  "bootstrap",
    "estimates (central params)":    "estimates",
}

_CLIMATE_LABEL_MAP = {
    "expected (central projections)": "expected",
    "uncertain (bootstrapped)":       "uncertain",
}

_DISC_MAP = {
    "Growth-adjusted (prtp=2%, η=1.5)": {"prtp": "2",  "eta": "1p5", "dr": "NA"},
    "Growth-adjusted (prtp=1%, η=1.5)": {"prtp": "1",  "eta": "1p5", "dr": "NA"},
    "Growth-adjusted (prtp=2%, η=0.7)": {"prtp": "2",  "eta": "0p7", "dr": "NA"},
    "Growth-adjusted (prtp=1%, η=0.7)": {"prtp": "1",  "eta": "0p7", "dr": "NA"},
    "Fixed 3%":                          {"prtp": "NA", "eta": "NA",  "dr": "3"},
    "Fixed 5%":                          {"prtp": "NA", "eta": "NA",  "dr": "5"},
}

_PERCENTILE_MAP = {
    "16.7% (optimistic)":  0,
    "50.0% (central)":     1,
    "83.3% (pessimistic)": 2,
}


_db = None


def _get_db():
    global _db
    if _db is None:
        import pandas as pd
        _db = pd.read_pickle(_PKL_PATH)
    return _db


def _lookup(df, iso3, run, dmgfuncpar, climate, ssp, rcp, disc):
    """Returns (values, reason) where values is (lo, med, hi) or None.
    reason: "ok" | "na" | "missing"
    """
    import pandas as pd
    key = (iso3, run, dmgfuncpar, climate, ssp, rcp, disc["prtp"], disc["eta"], disc["dr"])
    try:
        row = df.loc[key]
        lo, med, hi = row["16.7%"], row["50%"], row["83.3%"]
        if pd.isna(lo) or pd.isna(med) or pd.isna(hi):
            return None, "na"
        return (float(lo), float(med), float(hi)), "ok"
    except KeyError:
        return None, "missing"

CHUNK = "social_cost_data"

_SSP_OPTIONS = [
    "SSP1 (Sustainability)",
    "SSP2 (Middle of the Road)",
    "SSP3 (Regional Rivalry)",
    "SSP4 (Inequality)",
    "SSP5 (Fossil-fueled Development)",
]

_RCP_OVERRIDE_OPTIONS = [
    "Closest RCP (default)",
    "RCP4.5 (≈ +2.5°C in 2100)",
    "RCP6.0 (≈ +3°C in 2100)",
    "RCP8.5 (≈ +4.5°C in 2100)",
]

_DMG_FUNC_OPTIONS = [
    "BHM SR (Short Run)",
    "BHM RP SR (Rich/Poor Short Run)",
    "BHM LR (Long Run)",
    "BHM RP LR (Rich/Poor Long Run)",
]

_DMG_PARAM_OPTIONS = [
    "bootstrap (full uncertainty)",
    "estimates (central params)",
]

_CLIMATE_MODEL_OPTIONS = [
    "expected (central projections)",
    "uncertain (bootstrapped)",
]

_DISCOUNTING_OPTIONS = [
    "Growth-adjusted (prtp=2%, η=1.5)",
    "Growth-adjusted (prtp=1%, η=1.5)",
    "Growth-adjusted (prtp=2%, η=0.7)",
    "Growth-adjusted (prtp=1%, η=0.7)",
    "Fixed 3%",
    "Fixed 5%",
]

_PERCENTILE_OPTIONS = [
    "16.7% (optimistic)",
    "50.0% (central)",
    "83.3% (pessimistic)",
]

RICKE_FIELDS: list[FieldDef | Section] = [
    Section("Socioeconomic & Climate Scenarios"),
    FieldDef(
        "iso3",
        "Country (ISO3)",
        "The country for which to calculate the social cost. 'WLD' represents the global aggregate.",
        "combo",
        options=["WLD"],
        required=True,
    ),
    FieldDef(
        "ssp",
        "Socioeconomic Pathway (SSP)",
        "Assumptions on future population, GDP, and energy use.",
        "combo",
        options=_SSP_OPTIONS,
        required=True,
    ),
    FieldDef(
        "rcp",
        "Climate Trajectory (RCP)",
        "Representative Concentration Pathway. Choose 'Closest RCP' to use the paper's default pairing.",
        "combo",
        options=_RCP_OVERRIDE_OPTIONS,
        required=True,
    ),
    Section("Damage Function & Model Parameters"),
    FieldDef(
        "dmg_func",
        "Damage Function",
        "The empirical model used to relate temperature change to economic damage.",
        "combo",
        options=_DMG_FUNC_OPTIONS,
        required=True,
    ),
    FieldDef(
        "dmg_params",
        "Damage Parameters",
        "Whether to use bootstrapped uncertainty or central parameter estimates.",
        "combo",
        options=_DMG_PARAM_OPTIONS,
        required=True,
    ),
    FieldDef(
        "climate_uncertainty",
        "Climate Uncertainty",
        "Whether to use expected climate projections or bootstrapped uncertainty.",
        "combo",
        options=_CLIMATE_MODEL_OPTIONS,
        required=True,
    ),
    Section("Discounting & Valuation"),
    FieldDef(
        "discounting",
        "Discounting Approach",
        "The method for calculating the present value of future damages (Pure Rate of Time Preference and Elasticity of Marginal Utility).",
        "combo",
        options=_DISCOUNTING_OPTIONS,
        required=True,
    ),
    FieldDef(
        "percentile",
        "Percentile",
        "The statistical percentile of the SCC distribution to use.",
        "combo",
        options=_PERCENTILE_OPTIONS,
        required=True,
    ),
    Section("Currency Adjustment"),
    FieldDef(
        "usd_to_local_rate",
        "USD Conversion Rate",
        "Conversion rate for international scientific model outputs (base is USD 2015).",
        "float",
        options=(1e-6, 1e6, DECIMAL_PLACES),
        unit="(Currency/USD)",
        warn=(
            0.0001,
            None,
            "USD to Local Currency Conversion Rate is 0 - the Ricke et al. social cost of carbon will result in 0 in the local currency; enter the current USD-to-local exchange rate",
        ),
    ),
    Section("Inflation Adjustment (CPI)"),
    FieldDef(
        "cpi_ratio",
        "CPI Ratio (current / 2018)",
        "The Ricke et al. paper was published in 2018. Apply a CPI ratio (current year CPI ÷ 2018 CPI) to adjust the output for inflation. Set to 1.0 to use the original 2018 values.",
        "float",
        options=(0.0, 100.0, DECIMAL_PLACES),
        default=1.0,
        warn=(
            0.0001,
            None,
            "CPI Ratio is 0 — no inflation adjustment will be applied to the SCC value",
        ),
    ),
]


class RickeWidget(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name=CHUNK)
        build_form(self, RICKE_FIELDS)

        # ── result labels (inside scroll, after last field) ───────────────────
        self._lbl_scc = QLabel("—")
        self._lbl_range = QLabel("")
        self._lbl_params = QLabel("")
        self._lbl_status = QLabel("Fill all fields above to compute.")

        for lbl in (self._lbl_scc, self._lbl_range, self._lbl_params, self._lbl_status):
            lbl.setWordWrap(True)

        self._lbl_scc.setStyleSheet(f"color: {get_token('text')};")
        self._lbl_range.setStyleSheet(f"color: {get_token('text_secondary')};")
        self._lbl_params.setStyleSheet(f"color: {get_token('text_secondary')};")
        self._lbl_status.setStyleSheet(f"color: {get_token('text_secondary')};")

        for lbl in (self._lbl_scc, self._lbl_range, self._lbl_params, self._lbl_status):
            self.form.addRow(lbl)


        # ── clear button (inside form, same pattern as demolition/traffic_data) ─
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 10, 0, 10)
        self._btn_clear = QPushButton("Clear All")
        self._btn_clear.setMinimumHeight(35)
        self._btn_clear.clicked.connect(self._clear_all)
        btn_layout.addWidget(self._btn_clear)
        self.form.addRow(btn_row)

        self._populate_iso3()
        self._connect_combo_logging()

    def _populate_iso3(self):
        try:
            df = _get_db()
            iso3_list = sorted(df.index.get_level_values("ISO3").unique())
            combo = self._field_map["iso3"]
            combo.clear()
            combo.addItem("-- select --")
            combo.addItems(iso3_list)
        except Exception as e:
            print(f"[RickeWidget] failed to load ISO3 list: {e}")

    def _connect_combo_logging(self):
        from PySide6.QtWidgets import QComboBox, QDoubleSpinBox
        for widget in self._field_map.values():
            if isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(lambda _: self._print_ricke_cost())
            elif isinstance(widget, QDoubleSpinBox):
                widget.valueChanged.connect(lambda _: self._print_ricke_cost())

    def _print_ricke_cost(self):
        fm = self._field_map

        iso3      = fm["iso3"].currentText()
        ssp_label = fm["ssp"].currentText()
        rcp_label = fm["rcp"].currentText()
        dmg_label = fm["dmg_func"].currentText()
        par_label = fm["dmg_params"].currentText()
        cli_label = fm["climate_uncertainty"].currentText()
        dis_label = fm["discounting"].currentText()
        pct_label = fm["percentile"].currentText()

        # ── guard: all required fields must be filled ─────────────────────────
        required = {
            "Country":             iso3,
            "SSP":                 ssp_label,
            "RCP":                 rcp_label,
            "Damage Function":     dmg_label,
            "Damage Parameters":   par_label,
            "Climate Uncertainty": cli_label,
            "Discounting":         dis_label,
            "Percentile":          pct_label,
        }
        unfilled = [name for name, val in required.items() if val == _PLACEHOLDER]
        if unfilled:
            self._lbl_scc.setText("—")
            self._lbl_scc.setStyleSheet(f"color: {get_token('text')};")
            self._lbl_range.setText("")
            self._lbl_params.setText("")
            self._lbl_status.setText(f"Waiting for: {', '.join(unfilled)}")
            self._lbl_status.setStyleSheet(f"color: {get_token('text_secondary')};")
            print(f"[RickeWidget] waiting for: {', '.join(unfilled)}")
            return

        # ── exact lookups — no assumptions ────────────────────────────────────
        ssp = _SSP_LABEL_MAP.get(ssp_label)
        rcp_raw = _RCP_LABEL_MAP.get(rcp_label)
        rcp = rcp_raw if rcp_raw is not None else _CLOSEST_RCP[ssp]
        run = _DMG_FUNC_LABEL_MAP.get(dmg_label)
        dmgfuncpar = _DMG_PARAMS_LABEL_MAP.get(par_label)
        climate = _CLIMATE_LABEL_MAP.get(cli_label)
        disc = _DISC_MAP.get(dis_label)
        pct_idx = _PERCENTILE_MAP.get(pct_label)

        missing = [k for k, v in {
            "ssp": ssp, "run": run, "dmgfuncpar": dmgfuncpar,
            "climate": climate, "disc": disc, "pct_idx": pct_idx,
        }.items() if v is None]
        if missing:
            self._lbl_status.setText(f"Unmapped values: {', '.join(missing)}")
            print(f"[RickeWidget] unmapped keys: {', '.join(missing)}")
            return

        # ── DB lookup ─────────────────────────────────────────────────────────
        try:
            df = _get_db()
        except Exception as e:
            self._lbl_status.setText(f"DB error: {e}")
            print(f"[RickeWidget] DB load error: {e}")
            return

        result, reason = _lookup(df, iso3, run, dmgfuncpar, climate, ssp, rcp, disc)

        rcp_display = rcp_label if rcp_raw is not None else f"{rcp_label} → {rcp}"
        summary = (
            f"Country: {iso3}   ·   SSP: {ssp_label}   ·   RCP: {rcp_display}\n"
            f"Damage Function: {dmg_label}   ·   Parameters: {par_label}   ·   Climate: {cli_label}\n"
            f"Discounting: {dis_label}   ·   Percentile: {pct_label}"
        )

        if reason in ("na", "missing"):
            msg = (
                "No data available for this combination in the DB — please change one or more selections above."
                if reason == "na" else
                "This combination was not found in the DB — please change one or more selections above."
            )
            self._lbl_scc.setText("No Result")
            self._lbl_scc.setStyleSheet(f"color: {get_token('danger')};")
            self._lbl_range.setText("")
            self._lbl_params.setText(summary)
            self._lbl_params.setStyleSheet(f"color: {get_token('text_secondary')};")
            self._lbl_status.setText(msg)
            self._lbl_status.setStyleSheet(f"color: {get_token('danger')};")
            print(f"[RickeWidget] {msg}")
        else:
            lo, med, hi = result
            displayed = result[pct_idx]
            cpi_ratio = self._field_map["cpi_ratio"].value() if "cpi_ratio" in self._field_map else 1.0
            adjusted = displayed * cpi_ratio
            adj_lo, adj_hi = lo * cpi_ratio, hi * cpi_ratio
            cpi_applied = abs(cpi_ratio - 1.0) > 1e-6

            if cpi_applied:
                scc_text = f"{adjusted:,.4f} USD / tCO₂   (CPI-adjusted from {displayed:,.4f} in 2018 USD)"
                ci_text  = (
                    f"66.7% Confidence Interval:  {adj_lo:,.4f}  –  {adj_hi:,.4f} USD / tCO₂  (CPI-adjusted)\n"
                    f"                             {lo:,.4f}  –  {hi:,.4f} USD / tCO₂  (2018 USD)"
                )
            else:
                scc_text = f"{displayed:,.4f} USD / tCO₂   (2018 USD)"
                ci_text  = f"66.7% Confidence Interval:  {lo:,.4f}  –  {hi:,.4f} USD / tCO₂"

            self._lbl_scc.setText(scc_text)
            self._lbl_scc.setStyleSheet(f"color: {get_token('success')};")
            self._lbl_range.setText(ci_text)
            self._lbl_range.setStyleSheet(f"color: {get_token('text_secondary')};")
            self._lbl_params.setText(summary)
            self._lbl_params.setStyleSheet(f"color: {get_token('text_secondary')};")
            self._lbl_status.setText("")
            print(f"[RickeWidget] SCC = {adjusted:,.4f} USD/tCO₂ (CPI ratio={cpi_ratio}, 2018 base={displayed:,.4f})  CI=[{adj_lo:,.4f}–{adj_hi:,.4f}]")

    def _clear_all(self):
        if not confirm_clear_all(self):
            return
        for widget in self._field_map.values():
            from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QSpinBox, QLineEdit, QCheckBox, QTextEdit
            if isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(widget.minimum())
            elif isinstance(widget, QSpinBox):
                widget.setValue(widget.minimum())
            elif isinstance(widget, (QLineEdit, QTextEdit)):
                widget.clear()
            elif isinstance(widget, QCheckBox):
                widget.setChecked(False)

    def freeze(self, frozen: bool = True):
        freeze_form(self._field_map, frozen)
        self._btn_clear.setEnabled(not frozen)

    def validate(self):
        result = validate_form(RICKE_FIELDS, self)
        if result["errors"]:
            return result

        # all required fields filled — also validate the DB combination
        fm = self._field_map
        ssp = _SSP_LABEL_MAP.get(fm["ssp"].currentText())
        rcp_raw = _RCP_LABEL_MAP.get(fm["rcp"].currentText())
        rcp = rcp_raw if rcp_raw is not None else _CLOSEST_RCP.get(ssp, "rcp60")
        run = _DMG_FUNC_LABEL_MAP.get(fm["dmg_func"].currentText())
        dmgfuncpar = _DMG_PARAMS_LABEL_MAP.get(fm["dmg_params"].currentText())
        climate = _CLIMATE_LABEL_MAP.get(fm["climate_uncertainty"].currentText())
        disc = _DISC_MAP.get(fm["discounting"].currentText())
        iso3 = fm["iso3"].currentText()

        if all(v is not None for v in (ssp, run, dmgfuncpar, climate, disc)):
            try:
                _, reason = _lookup(_get_db(), iso3, run, dmgfuncpar, climate, ssp, rcp, disc)
                if reason in ("na", "missing"):
                    result["errors"].append(
                        "Selected combination has no data in the DB — change this combination."
                    )
            except Exception:
                pass

        return result

    def clear_validation(self):
        clear_field_styles(self._field_map)
