# Validation

Validation uses the WSL base environment. The C++ and Python implementations
are compared statistically, not event-for-event, because their random-number
engines differ. The acceptance run uses at least 1,000 cells and records the
exact Git commit, model hashes, seed, duration, and parameters.

Acceptance thresholds are 10% for key means/medians and 5 percentage points for
survival. This file will contain measured results after the implementation and
benchmark executables are available; placeholders are not presented as data.
