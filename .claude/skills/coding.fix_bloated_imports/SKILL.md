---
description: Fix Python imports of large packages needed only for few functions in a module
model: haiku
---

- I pass you one or more files `<FILES>` and one or more packages `<PACKAGES>` that
  are large to import (e.g., `ipython`, `pandas`) and needed in only a few functions

- In `<FILES>`, use a conditional import for type checking and lazy imports for
  `<PACKAGES>`
  - E.g., transform
    ```python
    def make_slider() -> "ipywidgets.IntSlider":
        import ipywidgets
        ...
    ```
    into
    ```python
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        import ipywidgets

    def make_slider() -> "ipywidgets.IntSlider":
        import ipywidgets
        ...
    ```

- Use forward references only for the package types, not for the whole expression
  - **Bad** (quotes the whole expression as one string)
    ```python
    "Tuple[Union[ipywidgets.FloatSlider, ipywidgets.IntSlider], ipywidgets.HBox]"
    ```
  - **Good** (quotes only the package types)
    ```python
    Tuple[Union["ipywidgets.FloatSlider", "ipywidgets.IntSlider"], "ipywidgets.HBox"]
    ```

- If most functions in `<FILES>` need `<PACKAGES>`, suggest not doing this transform

# Verification
- [ ] Confirm `<PACKAGES>` is imported only under `TYPE_CHECKING` or inside the
      functions that use it
- [ ] Confirm forward references quote only the package types, not full
      expressions
