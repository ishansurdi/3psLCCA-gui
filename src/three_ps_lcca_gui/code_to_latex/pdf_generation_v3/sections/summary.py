from ..document import paragraph, section


def summary_to_latex() -> str:
    return "\n\n".join([
        section("Summary and Conclusions"),
        paragraph(
            "The LCCA results indicate the relative contribution of construction, "
            "road user, and environmental costs, supporting informed and sustainable "
            "bridge planning decisions."
        ),
    ])

