from ..latex_helpers import paragraph, section


def _framework_figure() -> str:
    image_path = "../pdf_generation_v3/images/image_1.png"

    return "\n".join([
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.82\textwidth]{" + image_path + r"}",
        r"\caption{3PS Life Cycle Cost Assessment}",
        r"\end{figure}",
    ])


def introduction_to_latex() -> str:
    return "\n\n".join([
        section("Introduction to LCCA"),
        paragraph(
            "Life Cycle Cost Assessment evaluates the bridge across economic, "
            "social, and environmental cost components over the selected analysis "
            "period."
        ),
        _framework_figure(),
    ])
