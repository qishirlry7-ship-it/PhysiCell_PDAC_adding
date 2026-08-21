# Performance

Benchmarks run in the WSL base environment with release flags. Report CPU,
compiler, Git commit, model hashes, threads, active-cell count, simulated time,
SSA events, wall time, peak memory, and speedup.

Measured with WSL base, g++ 13, `-O3 -march=native -fopenmp`, 32 logical
processors reported by Windows, commit `ec78337`, and 50 vacuolar bacteria per
cell at time zero:

| Cells | Simulated | Threads | Wall time | Reactions | Throughput |
|---:|---:|---:|---:|---:|---:|
| 1 | 1 h | 1 | 0.00048 s | 2,204 | 4.59 M/s |
| 10 | 1 h | 1 | 0.00486 s | 22,589 | 4.65 M/s |
| 100 | 1 h | 1 | 0.0467 s | 226,548 | 4.85 M/s |
| 100 | 1 h | 4 | 0.0124 s | 226,548 | 18.27 M/s |
| 1,000 | 24 h | 4 | 4.71 s | 76,164,221 | 16.16 M/s |
| 10,000 | 1 h | 4 | 1.44 s | 22,531,966 | 15.64 M/s |
| 10,000 | 24 h | 8 | 28.76 s | 761,534,412 | 26.48 M/s |

The one-minute full PhysiCell correctness smoke run with 1,724 cells took
4.57 s. It is not an on/off overhead comparison. The controlled disabled,
enabled-idle, and 1%/10%/100% infection matrix remains pending a normalized
production initial-cell file. Raw benchmark CSV files are intentionally ignored.

Full PhysiCell 24-hour stress scenario, WSL base, 4 OpenMP threads, 100 initial
tumor cells, and 150 vacuolar bacteria per initial cell:

| Initial cells | Observed PetriNet states | Simulated | Wall time | Metrics rows |
|---:|---:|---:|---:|---:|
| 100 | 112 | 24 h | 25.05 s | 25,453 |

The 112 states comprise 100 initial cells and 12 daughters. This timing
includes PhysiCell microenvironment/cell updates and per-cell CSV metrics, not
only standalone SSA execution.
