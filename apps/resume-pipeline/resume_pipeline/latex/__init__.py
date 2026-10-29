"""LaTeX validation for untrusted templates (RG-021, RG-035).

Compilation itself lives in `resume_pipeline.services.latex`, which calls the containerised
Tectonic service. This package is the layer that runs before a request is ever sent, and on every
template write.
"""

from resume_pipeline.latex.validate import (
    MAX_TEX_BYTES,
    Problem,
    assert_valid_tex,
    validate_tex,
)

__all__ = ["MAX_TEX_BYTES", "Problem", "assert_valid_tex", "validate_tex"]
