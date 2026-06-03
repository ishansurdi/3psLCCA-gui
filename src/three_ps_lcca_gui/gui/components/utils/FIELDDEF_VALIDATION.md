# FieldDef Validation Guide

This guide explains how to use `FieldDef` to implement automated validation (Errors and Warnings) in the LCCA GUI.

---

## 1. Errors (Required Fields)

Errors are "hard" validation failures that typically block calculations. They are triggered by setting `required=True` in a `FieldDef`.

### For Text Fields (`text`, `textarea`)
A text field is in error if it is empty or only contains whitespace.

```python
FieldDef(
    key="project_name",
    title="Project Name",
    explanation="Enter the official name.",
    field_type="text",
    required=True  # Triggers error if blank
)
```

### For Numeric Fields (`int`, `float`)
By default, numeric fields are never "missing" because `0` is a valid number. However, you can force a "required" state by providing an explicit `default` value:

```python
FieldDef(
    key="interest_rate",
    title="Interest Rate",
    explanation="Annual interest rate.",
    field_type="float",
    options=(0.0, 100.0, 2),
    default=0.0,    # If the value stays at 0.0 (the minimum),
    required=True   # it will trigger an Error: "enter a value above the minimum"
)
```

---

## 2. Warnings (Range Checks)

Warnings are "soft" validation hints. They highlight unusual values with an orange border but allow the user to proceed.

### Inline Warnings (Preferred)
You can define warning thresholds directly inside the `FieldDef` using the `warn` parameter.

```python
FieldDef(
    key="discount_rate",
    title="Discount Rate",
    explanation="Social discount rate.",
    field_type="float",
    options=(0.0, 100.0, 2),
    # warn = (low_threshold, high_threshold, [low_msg], [high_msg])
    warn=(0.01, 15.0, "Rate is unusually low", "Rate is unusually high")
)
```

### Warning Tuple Formats
The `warn` tuple can take several shapes:
- `(low, high)`: Uses generic "value is unusual" messages.
- `(low, high, msg)`: Uses the same `msg` for both low and high violations.
- `(low, high, low_msg, high_msg)`: Different messages for each direction.
- `(None, high, ...)`: Only checks the upper bound.

---

## 3. Implementation in the Page

To activate validation, your page's `validate()` method must call `validate_form`.

```python
from .utils.form_builder.form_definitions import FieldDef
from .utils.validation_helpers import validate_form

FIELDS = [
    FieldDef("name", "Name", "", "text", required=True),
    FieldDef("qty", "Quantity", "", "int", options=(0, 100), warn=(1, 50))
]

class MyPage(ScrollableForm):
    def validate(self) -> dict:
        # validate_form handles required checks and warn ranges automatically
        return validate_form(FIELDS, self)
```

---

## 4. Summary Table

| Field Type | Property | Condition | Result | Border |
| :--- | :--- | :--- | :--- | :--- |
| **Text** | `required=True` | `text().strip() == ""` | **Error** | Red |
| **Numeric** | `required=True` & `default` | `value() == minimum()` | **Error** | Red |
| **Numeric** | `warn=(low, high)` | `value() < low` or `> high` | **Warning** | Orange |

> **Note:** If a field has an **Error**, the **Warning** check is skipped for that field to keep the UI focused on the most critical issue.
