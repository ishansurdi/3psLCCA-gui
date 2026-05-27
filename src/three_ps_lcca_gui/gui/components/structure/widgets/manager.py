from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QGroupBox,
    QInputDialog,
    QMessageBox,
    QLabel,
    QFrame,
)
from PySide6.QtCore import Qt, QTimer
import time
import uuid
import datetime
import traceback

from .base_table import StructureTableWidget
from .material_dialog import MaterialDialog
from ...utils.definitions import UNIT_DISPLAY
from ...utils.validation_helpers import freeze_widgets
from ...utils.display_format import fmt, fmt_comma
from three_ps_lcca_gui.gui.styles import btn_danger


# ---------------------------------------------------------------------------
# StructureManagerWidget
# ---------------------------------------------------------------------------


class StructureManagerWidget(QWidget):
    def __init__(self, controller, chunk_name, default_components):
        super().__init__()
        self.controller = controller
        self.chunk_name = chunk_name
        self.default_components = default_components
        self.sections = {}
        self.data = {}

        self._frozen = False
        self._add_material_btns = []
        self._del_comp_btns = []

        self.main_layout = QVBoxLayout(self)

        # ── Summary bar ──────────────────────────────────────────────────
        summary_bar = QWidget()
        summary_layout = QHBoxLayout(summary_bar)
        summary_layout.setContentsMargins(4, 4, 4, 4)
        self.total_lbl = QLabel("Total: -")
        self.count_lbl = QLabel("Items: -")
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        summary_layout.addWidget(self.total_lbl)
        summary_layout.addWidget(sep)
        summary_layout.addWidget(self.count_lbl)
        summary_layout.addStretch()
        self.main_layout.addWidget(summary_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; }")

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)

        btn_layout = QHBoxLayout()
        self.add_comp_btn = QPushButton("+ Add Component")
        self.add_comp_btn.clicked.connect(self.add_new_component)
        btn_layout.addWidget(self.add_comp_btn)
        btn_layout.addStretch()
        self.main_layout.addLayout(btn_layout)

    def on_refresh(self):
        try:
            if not self.controller or not getattr(self.controller, "engine", None):
                return

            data = self.controller.engine.fetch_chunk(self.chunk_name) or {}

            if not data and self.default_components:
                for comp in self.default_components:
                    data[comp] = []
                self.controller.engine.stage_update(
                    chunk_name=self.chunk_name, data=data
                )

            info = self.controller.engine.fetch_chunk("general_info") or {}
            self._currency = str(info.get("project_currency", ""))
            self.data = data
            self.refresh_ui()
        except Exception as e:

            print(f"[ERROR] on_refresh crashed: {e}")
            traceback.print_exc()

    def refresh_ui(self):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        self.sections = {}
        self._add_material_btns = []
        self._del_comp_btns = []
        currency = getattr(self, "_currency", "")

        for comp_name, items in self.data.items():
            self.create_section(comp_name)
            table = self.sections.get(comp_name)
            if table:
                table.set_currency(currency)
                for original_index, item in enumerate(items):
                    if not item.get("state", {}).get("in_trash", False):
                        table.add_row(item, original_index)

        self.container_layout.addStretch()
        self.container.adjustSize()
        self._update_summary()

        if getattr(self, "_frozen", False):
            self.freeze(True)

    def _update_summary(self):
        total = 0.0
        count = 0
        for items in self.data.values():
            for item in items:
                if not item.get("state", {}).get("in_trash", False):
                    v = item.get("values", {})
                    total += float(v.get("quantity", 0) or 0) * float(
                        v.get("rate", 0) or 0
                    )
                    count += 1
        currency = getattr(self, "_currency", "")
        suffix = f" ({currency})" if currency else ""
        self.total_lbl.setText(f"Total{suffix}: {fmt_comma(total)}")
        self.count_lbl.setText(f"{count} item{'s' if count != 1 else ''}")

    def create_section(self, name):
        group = QGroupBox(name)
        g_layout = QVBoxLayout(group)

        table = StructureTableWidget(self, name)
        self.sections[name] = table

        btn_bar = QHBoxLayout()

        add_row_btn = QPushButton(f"Add Material to {name}")
        add_row_btn.clicked.connect(lambda checked=False, n=name: self.open_dialog(n))
        freeze_widgets(self._frozen, add_row_btn)
        self._add_material_btns.append(add_row_btn)

        del_btn = QPushButton("Delete Component")
        del_btn.setObjectName("deleteButton")
        del_btn.setStyleSheet(btn_danger())
        del_btn.clicked.connect(lambda checked=False, n=name: self.delete_component(n))
        freeze_widgets(self._frozen, del_btn)
        self._del_comp_btns.append(del_btn)

        btn_bar.addWidget(add_row_btn, 1)
        btn_bar.addWidget(del_btn)

        g_layout.addWidget(table)
        g_layout.addLayout(btn_bar)
        self.container_layout.addWidget(group)

    def add_material(self, comp_name, values_dict, is_trash=False):
        now = datetime.datetime.now().isoformat()

        included_carbon = values_dict.pop("_included_in_carbon_emission", True)
        included_recycling = values_dict.pop("_included_in_recyclability", True)
        allow_edit_checked = values_dict.pop("_allow_edit_checked", False)
        from_sor = values_dict.pop("_from_sor", False)
        sor_db_key = values_dict.pop("_sor_db_key", "")
        is_excel = values_dict.pop("_is_excel_import", False)
        values_dict.pop("_is_customized", None)
        db_original = values_dict.pop("_db_original", {})
        # `id` may come from an Excel CID#ID column - store it as a reference, not a value field
        _excel_ref_id = values_dict.pop("id", None)
        if _excel_ref_id and "sor_ref_id" not in db_original:
            db_original = dict(db_original)
            db_original["sor_ref_id"] = str(_excel_ref_id)

        # Compute source + source_db_key
        if is_excel:
            source = "excel"
            source_db_key = ""
        elif from_sor:
            is_custom = sor_db_key.startswith("custom::")
            clean_key = sor_db_key.removeprefix("custom::")
            source = "custom_db" if is_custom else "db"
            source_db_key = clean_key
        else:
            source = "manual"
            source_db_key = ""

        new_entry = {
            "id": str(uuid.uuid4()),
            "values": values_dict,
            "meta": {
                "created_on": now,
                "modified_on": now,
                "source": source,
                "source_db_key": source_db_key,
                "db_original": db_original,
            },
            "state": {
                "in_trash": is_trash,
                "included_in_carbon_emission": included_carbon,
                "included_in_recyclability": included_recycling,
                "allow_edit_checked": allow_edit_checked,
            },
        }

        current_data = self.controller.engine.fetch_chunk(self.chunk_name) or {}
        if comp_name not in current_data:
            current_data[comp_name] = []

        current_data[comp_name].append(new_entry)
        self.controller.engine.stage_update(
            chunk_name=self.chunk_name, data=current_data
        )
        self.save_current_state()

        if is_trash:
            self.on_refresh()
            return

        original_index = len(current_data[comp_name]) - 1
        self.data = current_data
        table = getattr(self, "sections", {}).get(comp_name)
        if table:
            table.insert_row_at_position(new_entry, original_index)
            self._update_summary()
        else:
            self.on_refresh()

    def _get_project_country(self) -> str:
        try:
            return (
                self.controller.get_chunk("general_info").get("project_country", "")
                or ""
            )
        except Exception:
            return ""

    def _get_project_sor_db(self) -> str:
        try:
            return (
                self.controller.get_chunk("general_info").get("sor_database", "") or ""
            )
        except Exception:
            return ""

    def _existing_names(self, comp_name) -> set:
        """Return lowercased active material names for comp_name."""
        data = self.controller.engine.fetch_chunk(self.chunk_name) or {}
        return {
            item.get("values", {}).get("material_name", "").strip().lower()
            for item in data.get(comp_name, [])
            if not item.get("state", {}).get("in_trash", False)
        }

    def open_dialog(self, comp_name):
        dialog = MaterialDialog(
            comp_name,
            self,
            country=self._get_project_country(),
            sor_db_key=self._get_project_sor_db(),
        )

        def _on_material_added(values):
            name = values.get("material_name", "").strip()
            if name.lower() in self._existing_names(comp_name):
                QMessageBox.warning(
                    self,
                    "Duplicate Name",
                    f'A material named "{name}" already exists in "{comp_name}".\n'
                    "Use a different name.",
                )
                return
            self.add_material(comp_name, values)
            dialog._reset_for_next(name)

        dialog.material_added.connect(_on_material_added)
        dialog.exec()

    def open_edit_dialog(self, comp_name, original_index):
        try:
            current_data = self.controller.engine.fetch_chunk(self.chunk_name) or {}
            items = current_data.get(comp_name, [])

            if original_index < len(items):
                item_to_edit = items[original_index]

                dialog = MaterialDialog(
                    comp_name,
                    self,
                    data=item_to_edit,
                    country=self._get_project_country(),
                    sor_db_key=self._get_project_sor_db(),
                )
                if dialog.exec():
                    new_values = dialog.get_values()

                    included_carbon = new_values.pop(
                        "_included_in_carbon_emission", True
                    )
                    included_recycling = new_values.pop(
                        "_included_in_recyclability", True
                    )
                    allow_edit_checked = new_values.pop("_allow_edit_checked", False)
                    new_values.pop("_from_sor", None)
                    new_values.pop("_sor_db_key", None)
                    new_values.pop("_is_customized", None)
                    new_values.pop("_is_excel_import", None)
                    # _db_original is the encoded snapshot from get_values()
                    new_db_original = new_values.pop("_db_original", None)

                    item_to_edit["values"] = new_values
                    now = datetime.datetime.now().isoformat()
                    item_to_edit["meta"]["modified_on"] = now
                    # Always overwrite snapshot- dialog rebuilds it fresh on each suggestion.
                    # Keep the existing encoded value when nothing changed (empty string
                    # means no DB source was involved this edit).
                    if new_db_original is not None:
                        item_to_edit["meta"]["db_original"] = new_db_original
                    item_to_edit["state"][
                        "included_in_carbon_emission"
                    ] = included_carbon
                    item_to_edit["state"][
                        "included_in_recyclability"
                    ] = included_recycling
                    item_to_edit["state"]["allow_edit_checked"] = allow_edit_checked

                    self.controller.engine.stage_update(
                        chunk_name=self.chunk_name, data=current_data
                    )
                    self.save_current_state()

                    def _do_edit():
                        self.data = current_data
                        table = getattr(self, "sections", {}).get(comp_name)
                        if table:
                            # Find the visual row whose col-6 UserRole matches original_index
                            visual_row = None
                            for r in range(table.rowCount()):
                                cell = table.item(r, 6)
                                if cell and cell.data(Qt.UserRole) == original_index:
                                    visual_row = r
                                    break

                            if visual_row is not None:
                                v = new_values
                                # Surgical update of cells 0-5
                                cells_updated = 0
                                for col, text in [
                                    (0, v.get("material_name", "New Item")),
                                    (1, fmt(v.get("quantity", 0))),
                                    (2, UNIT_DISPLAY.get(v.get("unit", "").lower(), v.get("unit", ""))),
                                    (3, fmt_comma(v.get("rate", 0))),
                                    (4, v.get("rate_source", "Manual")),
                                ]:
                                    it = table.item(visual_row, col)
                                    if it:
                                        it.setText(text)
                                        cells_updated += 1

                                try:
                                    rate = float(v.get("rate", 0) or 0)
                                    qty = float(v.get("quantity", 0) or 0)
                                    total = rate * qty
                                except (ValueError, TypeError):
                                    total = 0.0

                                it_total = table.item(visual_row, 5)
                                if it_total:
                                    it_total.setText(fmt_comma(total))
                                    cells_updated += 1

                                # If cells are missing (None), fallback to full refresh
                                if cells_updated < 6:
                                    self.on_refresh()
                                else:
                                    table.update_height()
                                    self._update_summary()
                            else:
                                self.on_refresh()
                        else:
                            self.on_refresh()

                    QTimer.singleShot(0, _do_edit)
        except Exception as e:

            print(f"[ERROR] open_edit_dialog crashed: {e}")
            traceback.print_exc()

    def toggle_trash_status(self, comp_name, data_index, should_trash):
        data = self.controller.engine.fetch_chunk(self.chunk_name) or {}
        if comp_name in data and len(data[comp_name]) > data_index:
            if "state" not in data[comp_name][data_index]:
                data[comp_name][data_index]["state"] = {}
            data[comp_name][data_index]["state"]["in_trash"] = should_trash
            self.data = data  # keep cached copy in sync for _update_summary

            self.controller.engine.stage_update(chunk_name=self.chunk_name, data=data)
            self.save_current_state()

            def _do_refresh():
                table = self.sections.get(comp_name)
                if table:
                    table.remove_row_by_index(data_index)
                self._update_summary()
                main_view = self.window().findChild(QWidget, "StructureTabView")
                if main_view:
                    main_view.update_trash_count()

            QTimer.singleShot(0, _do_refresh)

    def add_new_component(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("New Component")
        dialog.setLabelText("Enter Component Name:")
        dialog.setOkButtonText("Add")
        ok = dialog.exec()
        name = dialog.textValue()
        if ok and name.strip():
            clean_name = name.strip()
            current_data = self.controller.engine.fetch_chunk(self.chunk_name) or {}
            if any(k.lower() == clean_name.lower() for k in current_data):
                QMessageBox.warning(
                    self,
                    "Duplicate Component",
                    f'A component named "{clean_name}" already exists.',
                )
                return
            current_data[clean_name] = []
            self.controller.engine.stage_update(
                chunk_name=self.chunk_name, data=current_data
            )
            self.create_section(clean_name)
            self.save_current_state()

    def delete_component(self, name):
        current_data = self.controller.engine.fetch_chunk(self.chunk_name) or {}
        items = current_data.get(name, [])
        active_count = sum(
            1 for i in items if not i.get("state", {}).get("in_trash", False)
        )

        msg = f'Delete component "{name}"?'
        if active_count:
            msg += f"\n\n{active_count} material(s) inside will be permanently removed."

        reply = QMessageBox.question(
            self,
            "Delete Component",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        current_data.pop(name, None)
        self.controller.engine.stage_update(chunk_name=self.chunk_name, data=current_data)
        self.save_current_state()
        self.data = current_data
        self.refresh_ui()

    def freeze(self, frozen: bool = True):
        self._frozen = frozen
        freeze_widgets(frozen, self.add_comp_btn, *self._add_material_btns, *self._del_comp_btns)
        for table in self.sections.values():
            table.freeze(frozen)

    def save_current_state(self):
        if self.controller and self.controller.engine:
            eng = self.controller.engine
            eng._last_keystroke_time = time.time()
            eng._has_unsaved_changes = True
            try:
                eng.on_dirty(True)
            except Exception:
                pass


