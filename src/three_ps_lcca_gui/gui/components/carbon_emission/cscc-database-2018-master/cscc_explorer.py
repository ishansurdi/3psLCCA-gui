import tkinter as tk
from tkinter import ttk
from pathlib import Path
import pandas as pd

PKL_PATH = Path(__file__).parent / "cscc_db.pkl"

# Closest RCP for each SSP (default pairing from the paper)
CLOSEST_RCP = {
    "SSP1": "rcp60",
    "SSP2": "rcp60",
    "SSP3": "rcp85",
    "SSP4": "rcp60",
    "SSP5": "rcp85",
}

DMG_MAP = {
    "BHM SR":    "bhm_sr",
    "BHM RP SR": "bhm_richpoor_sr",
    "BHM LR":    "bhm_lr",
    "BHM RP LR": "bhm_richpoor_lr",
}

DISC_MAP = {
    "Growth-adjusted (prtp=2%, η=1.5)": {"prtp": "2", "eta": "1p5", "dr": "NA"},
    "Growth-adjusted (prtp=1%, η=1.5)": {"prtp": "1", "eta": "1p5", "dr": "NA"},
    "Growth-adjusted (prtp=2%, η=0.7)": {"prtp": "2", "eta": "0p7", "dr": "NA"},
    "Growth-adjusted (prtp=1%, η=0.7)": {"prtp": "1", "eta": "0p7", "dr": "NA"},
    "Fixed 3%":                          {"prtp": "NA", "eta": "NA", "dr": "3"},
    "Fixed 5%":                          {"prtp": "NA", "eta": "NA", "dr": "5"},
}

SSP_LABELS = ["SSP1/RCP60", "SSP2/RCP60", "SSP3/RCP85", "SSP4/RCP60", "SSP5/RCP85"]
SSP_VALUES = ["SSP1", "SSP2", "SSP3", "SSP4", "SSP5"]

RCP_OVERRIDE_LABELS = [
    "Closest RCP (default)",
    "RCP4.5  (≈ +2.5°C in 2100)",
    "RCP6.0  (≈ +3°C in 2100)",
    "RCP8.5  (≈ +4.5°C in 2100)",
]
RCP_OVERRIDE_VALUES = [None, "rcp45", "rcp60", "rcp85"]

DMG_FUNC_LABELS = ["bootstrap (full uncertainty)", "estimates (central params)"]
DMG_FUNC_VALUES = ["bootstrap", "estimates"]

CLIMATE_LABELS = ["expected (central projections)", "uncertain (bootstrapped)"]
CLIMATE_VALUES = ["expected", "uncertain"]

PERCENTILE_LABELS = ["16.7%  (optimistic)", "50%  (central)", "83.3%  (pessimistic)"]
PERCENTILE_IDX    = [0, 1, 2]


def load_index():
    """Return (df, iso3_list).  df has a 9-level MultiIndex for O(log n) lookups."""
    df = pd.read_pickle(PKL_PATH)
    iso3_list = sorted(df.index.get_level_values("ISO3").unique())
    return df, iso3_list


def lookup_gscc(df, iso3, run, dmgfuncpar, climate, ssp, rcp, disc):
    key = (iso3, run, dmgfuncpar, climate, ssp, rcp, disc["prtp"], disc["eta"], disc["dr"])
    try:
        row = df.loc[key]
        lo, med, hi = row["16.7%"], row["50%"], row["83.3%"]
        if pd.isna(lo) or pd.isna(med) or pd.isna(hi):
            return None
        return float(lo), float(med), float(hi)
    except KeyError:
        return None


class CSCCExplorer(tk.Tk):
    def __init__(self, index, iso3_list):
        super().__init__()
        self.index = index
        self.iso3_list = iso3_list
        self.title("Country-level Social Cost of Carbon — Explorer")
        self.resizable(False, False)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        PAD = dict(padx=12, pady=6)
        IPAD = dict(ipadx=4, ipady=2)

        # ── Title ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg="#2c3e50")
        hdr.pack(fill="x")
        tk.Label(
            hdr,
            text="Country-level Social Cost of Carbon",
            font=("Helvetica", 16, "bold"),
            fg="white", bg="#2c3e50",
        ).pack(side="left", **PAD)
        tk.Label(
            hdr,
            text="Database Explorer",
            font=("Helvetica", 13),
            fg="#bdc3c7", bg="#2c3e50",
        ).pack(side="left", pady=6)

        main = tk.Frame(self, padx=16, pady=10)
        main.pack(fill="both")

        # ── Country selection ────────────────────────────────────────────────
        self.iso3_var = tk.StringVar(value="WLD")
        grp_country = ttk.LabelFrame(main, text="Country  (ISO3)")
        grp_country.pack(fill="x", pady=(8, 4))
        country_row = tk.Frame(grp_country)
        country_row.pack(anchor="w", padx=8, pady=6)
        self._iso3_cb = ttk.Combobox(
            country_row,
            textvariable=self.iso3_var,
            values=self.iso3_list,
            state="readonly", width=12,
        )
        self._iso3_cb.pack(side="left")
        self._iso3_cb.bind("<<ComboboxSelected>>", lambda _: self._refresh())
        tk.Label(country_row, text="  (WLD = global aggregate)", fg="#7f8c8d").pack(side="left")

        # ── Future projection (SSP) ──────────────────────────────────────────
        self.ssp_var = tk.StringVar(value="SSP2")
        grp_ssp = ttk.LabelFrame(main, text="Future projection  (SSP / RCP)")
        grp_ssp.pack(fill="x", pady=(8, 4))
        btn_row = tk.Frame(grp_ssp)
        btn_row.pack(anchor="w", padx=8, pady=6)
        self._ssp_btns = {}
        for label, val in zip(SSP_LABELS, SSP_VALUES):
            b = tk.Button(
                btn_row, text=label, width=12,
                relief="raised", bd=2,
                command=lambda v=val: self._set_ssp(v),
            )
            b.pack(side="left", padx=3)
            self._ssp_btns[val] = b

        # RCP override sub-option
        self.rcp_override_var = tk.IntVar(value=0)
        rcp_row = tk.Frame(grp_ssp)
        rcp_row.pack(anchor="w", padx=8, pady=(0, 6))
        tk.Label(rcp_row, text="RCP override:").pack(side="left")
        for i, lbl in enumerate(RCP_OVERRIDE_LABELS):
            tk.Radiobutton(
                rcp_row, text=lbl, variable=self.rcp_override_var,
                value=i, command=self._refresh,
            ).pack(side="left", padx=6)

        # ── Damage function ──────────────────────────────────────────────────
        self.dmg_var = tk.StringVar(value="BHM SR")
        grp_dmg = ttk.LabelFrame(main, text="Damage function")
        grp_dmg.pack(fill="x", pady=4)
        dmg_row = tk.Frame(grp_dmg)
        dmg_row.pack(anchor="w", padx=8, pady=6)
        self._dmg_btns = {}
        for label in DMG_MAP:
            b = tk.Button(
                dmg_row, text=label, width=12,
                relief="raised", bd=2,
                command=lambda v=label: self._set_dmg(v),
            )
            b.pack(side="left", padx=3)
            self._dmg_btns[label] = b

        # ── Discounting ──────────────────────────────────────────────────────
        self.disc_var = tk.StringVar(value=list(DISC_MAP)[0])
        grp_disc = ttk.LabelFrame(main, text="Discounting")
        grp_disc.pack(fill="x", pady=4)
        disc_cb = ttk.Combobox(
            grp_disc,
            textvariable=self.disc_var,
            values=list(DISC_MAP),
            state="readonly", width=42,
        )
        disc_cb.pack(anchor="w", padx=10, pady=8)
        disc_cb.bind("<<ComboboxSelected>>", lambda _: self._refresh())

        # ── Advanced options ─────────────────────────────────────────────────
        grp_adv = ttk.LabelFrame(main, text="Advanced options")
        grp_adv.pack(fill="x", pady=4)
        adv_inner = tk.Frame(grp_adv)
        adv_inner.pack(anchor="w", padx=8, pady=6)

        self.dmgfuncpar_var = tk.IntVar(value=0)
        tk.Label(adv_inner, text="Damage params:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        for i, lbl in enumerate(DMG_FUNC_LABELS):
            tk.Radiobutton(
                adv_inner, text=lbl,
                variable=self.dmgfuncpar_var, value=i,
                command=self._refresh,
            ).grid(row=0, column=i + 1, sticky="w", padx=6)

        self.climate_var = tk.IntVar(value=0)
        tk.Label(adv_inner, text="Climate:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        for i, lbl in enumerate(CLIMATE_LABELS):
            tk.Radiobutton(
                adv_inner, text=lbl,
                variable=self.climate_var, value=i,
                command=self._refresh,
            ).grid(row=1, column=i + 1, sticky="w", padx=6)

        # ── GSCC result ──────────────────────────────────────────────────────
        result_frame = tk.Frame(main, bg="#1a252f", relief="flat", bd=0)
        result_frame.pack(fill="x", pady=(14, 4))

        self.gscc_title_lbl = tk.Label(
            result_frame,
            text="Social Cost of Carbon — Global",
            font=("Helvetica", 11), fg="#bdc3c7", bg="#1a252f",
        )
        self.gscc_title_lbl.pack(pady=(10, 0))

        self.pct_var = tk.IntVar(value=1)
        pct_row = tk.Frame(result_frame, bg="#1a252f")
        pct_row.pack(pady=(4, 0))
        for i, lbl in enumerate(PERCENTILE_LABELS):
            tk.Radiobutton(
                pct_row, text=lbl,
                variable=self.pct_var, value=i,
                command=self._refresh,
                bg="#1a252f", fg="#bdc3c7",
                selectcolor="#2c3e50", activebackground="#1a252f",
            ).pack(side="left", padx=8)

        self.gscc_lbl = tk.Label(
            result_frame,
            text="—",
            font=("Helvetica", 28, "bold"),
            fg="#f1c40f", bg="#1a252f",
        )
        self.gscc_lbl.pack()

        self.gscc_range_lbl = tk.Label(
            result_frame,
            text="",
            font=("Helvetica", 12),
            fg="#ecf0f1", bg="#1a252f",
        )
        self.gscc_range_lbl.pack(pady=(0, 10))

        # ── Status bar ───────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="")
        tk.Label(
            main, textvariable=self.status_var,
            font=("Helvetica", 9), fg="#7f8c8d", anchor="w",
        ).pack(fill="x", pady=(6, 0))

        self._update_button_styles()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _set_ssp(self, val):
        self.ssp_var.set(val)
        self._update_button_styles()
        self._refresh()

    def _set_dmg(self, val):
        self.dmg_var.set(val)
        self._update_button_styles()
        self._refresh()

    def _update_button_styles(self):
        active_bg, active_fg = "#2980b9", "white"
        default_bg, default_fg = "SystemButtonFace", "black"

        ssp = self.ssp_var.get()
        for val, btn in self._ssp_btns.items():
            if val == ssp:
                btn.config(bg=active_bg, fg=active_fg, relief="sunken")
            else:
                btn.config(bg=default_bg, fg=default_fg, relief="raised")

        dmg = self.dmg_var.get()
        for lbl, btn in self._dmg_btns.items():
            if lbl == dmg:
                btn.config(bg=active_bg, fg=active_fg, relief="sunken")
            else:
                btn.config(bg=default_bg, fg=default_fg, relief="raised")

    def _refresh(self):
        iso3 = self.iso3_var.get()
        ssp = self.ssp_var.get()
        rcp_idx = self.rcp_override_var.get()
        rcp = RCP_OVERRIDE_VALUES[rcp_idx] or CLOSEST_RCP[ssp]

        run = DMG_MAP[self.dmg_var.get()]
        disc = DISC_MAP[self.disc_var.get()]
        dmgfuncpar = DMG_FUNC_VALUES[self.dmgfuncpar_var.get()]
        climate = CLIMATE_VALUES[self.climate_var.get()]

        result = lookup_gscc(self.index, iso3, run, dmgfuncpar, climate, ssp, rcp, disc)

        label = "Global" if iso3 == "WLD" else iso3
        self.gscc_title_lbl.config(text=f"Social Cost of Carbon — {label}")

        if result is None:
            self.gscc_lbl.config(text="N/A", fg="#e74c3c")
            self.gscc_range_lbl.config(text="No data for this combination")
            self.status_var.set(
                f"Query: ISO3={iso3}  run={run}  dmgfuncpar={dmgfuncpar}  climate={climate}"
                f"  SSP={ssp}  RCP={rcp}  prtp={disc['prtp']}  η={disc['eta']}  dr={disc['dr']}"
            )
        else:
            lo, med, hi = result
            displayed = result[self.pct_var.get()]
            self.gscc_lbl.config(
                text=f"{displayed:,.1f}  USD / tCO₂",
                fg="#f1c40f",
            )
            self.gscc_range_lbl.config(
                text=f"66.7% confidence interval:  [{lo:,.1f} ; {hi:,.1f}]"
            )
            self.status_var.set(
                f"ISO3={iso3}  run={run}  dmgfuncpar={dmgfuncpar}  climate={climate}"
                f"  SSP={ssp}  RCP={rcp}  prtp={disc['prtp']}  η={disc['eta']}  dr={disc['dr']}"
            )


def main():
    print("Loading data…")
    index, iso3_list = load_index()
    print(f"Indexed {len(index)} rows across {len(iso3_list)} countries.")
    app = CSCCExplorer(index, iso3_list)
    app.mainloop()


if __name__ == "__main__":
    main()
