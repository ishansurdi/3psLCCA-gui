from PySide6.QtWidgets import QFormLayout, QStackedWidget, QWidget

from ...base_widget import BaseDataWidget
from ...utils.form_builder.form_definitions import FieldDef
from ...utils.form_builder.form_builder import build_form
from .scc_tabs.ricke import RickeWidget
from .scc_tabs.custom import CustomWidget

_SELECTOR_FIELDS = [
    FieldDef("selector", "Mode", "", "combo", options=["K. Ricke et al. (Country-Level)", "Custom / Manual Override"], combo_placeholder=""),
]

_KEYS = ["ricke", "custom"]


class SCCWidget(BaseDataWidget):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="social_cost_data")

        # ── selector form (header) ─────────────────────────────────────────────
        header = QWidget()
        self.form = QFormLayout(header)
        self.form.setContentsMargins(24, 12, 24, 4)
        self.form.setSpacing(8)
        build_form(self, _SELECTOR_FIELDS)

        # ── stacked content ────────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._sub_a = RickeWidget(controller=controller)
        self._sub_b = CustomWidget(controller=controller)
        self._stack.addWidget(self._sub_a)  # index 0
        self._stack.addWidget(self._sub_b)  # index 1

        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(header)
        self.layout.addWidget(self._stack)

        self._field_map["selector"].currentIndexChanged.connect(self._stack.setCurrentIndex)

    def _active(self):
        return self._stack.currentWidget()

    def freeze(self, frozen: bool = True):
        self._field_map["selector"].setEnabled(not frozen)
        for sub in (self._sub_a, self._sub_b):
            sub.freeze(frozen)

    def validate(self) -> dict:
        result = self._active().validate()
        if isinstance(result, dict):
            return result
        return {"errors": [], "warnings": []}

    def get_data(self) -> dict:
        idx = self._field_map["selector"].currentIndex()
        key = _KEYS[idx]
        return {
            "chunk": "social_cost_data",
            "data": {
                "mode": key,
                "cost": self._active().get_cost(),
                "ricke": self._sub_a.get_data_dict(),
                "custom": self._sub_b.get_data_dict(),
            },
        }

    def load_data(self, data: dict):
        key = data.get("mode", "ricke")
        idx = _KEYS.index(key) if key in _KEYS else 0
        self._field_map["selector"].setCurrentIndex(idx)
        self._sub_a.load_data_dict(data.get("ricke", {}))
        self._sub_b.load_data_dict(data.get("custom", {}))
