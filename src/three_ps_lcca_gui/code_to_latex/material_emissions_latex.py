import pandas as pd

from ..gui.project_controller import ProjectController
# from ..gui.components.carbon_emission.widgets.material_emissions import CHUNKS
from .chunks import STRUCTURE_MATERIAL_CHUNKS 


def material_emissions_to_latex(controller: ProjectController) -> str:
    included_rows = []
    excluded_rows = []

    for chunk_id, category in STRUCTURE_MATERIAL_CHUNKS:
        data = controller.engine.fetch_chunk(chunk_id) or {}

        for comp_name, items in data.items():
            for item in items:
                if item.get("state", {}).get("in_trash", False):
                    continue

                values = item.get("values", {})
                state = item.get("state", {})

                quantity = float(values.get("quantity", 0) or 0)
                conversion_factor = float(values.get("conversion_factor", 1) or 1)
                emission_factor = float(values.get("carbon_emission", 0) or 0)
                total = quantity * conversion_factor * emission_factor

                row = [
                    category,
                    values.get("material_name", ""),
                    f"{quantity:.2f}",
                    values.get("unit", ""),
                    f"{conversion_factor:.2f}",
                    f"{emission_factor:.2f}",
                    values.get("carbon_unit", ""),
                ]

                if state.get("included_in_carbon_emission") is True:
                    included_rows.append(row + [f"{total:.2f}"])
                else:
                    excluded_rows.append(row)

    included_df = pd.DataFrame(
        included_rows,
        columns=["Cat.", "Material", "Qty", "Unit", "CF", "EF", "EF Unit", "Total"],
    )

    excluded_df = pd.DataFrame(
        excluded_rows,
        columns=["Cat.", "Material", "Qty", "Unit", "CF", "EF", "EF Unit"],
    )

    included_tex = included_df.to_latex(
        index=False,
        caption="Included in Carbon Emissions Calculation",
        label="tab:material_emissions_included",
        escape=True,
        longtable=True,
)

    excluded_tex = excluded_df.to_latex(
        index=False,
        caption="Excluded from Carbon Emissions Calculation",
        label="tab:material_emissions_excluded",
        escape=True,
        longtable=True,
    )

    return included_tex + "\n\n" + excluded_tex