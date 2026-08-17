# Performance

Benchmarks run in the WSL base environment with release flags. Report CPU,
compiler, Git commit, model hashes, threads, active-cell count, simulated time,
SSA events, wall time, peak memory, and speedup.

Required matrices are 1/10/100/1,000/10,000 active cells, 1/6/24 simulated
hours, and 1/2/4/8 OpenMP threads. Full PhysiCell runs compare disabled,
enabled-idle, and infected fractions. Results are added only after a measured
run; no estimates are labeled as measurements.
