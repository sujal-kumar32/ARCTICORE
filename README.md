# Integrated Polar Expedition Logistics and Asset Management System

SMART INDIA HACKATHON 2026 — PS ID: SIH26062 — Ministry of Earth Sciences

This project is a local, transparent optimization and planning system for allocating polar expedition cargo across multiple trips. All scenarios are synthetic and are not official MoES cargo manifests.

## Features

- 50 reproducible scenarios with 200 cargo items each
- Greedy-by-priority baseline
- Beam-search heuristic AI planner
- Partial and multiple-trip cargo allocation
- Weight, volume and demand validation
- Loading sequence generation
- Priority fulfilment, capacity utilization and unmet critical-demand metrics
- Streamlit dashboard
- CSV, JSON and PDF experiment reports
- Automated Pytest suite

## Requirements

- Windows 11
- Python 3.11 or newer
- Internet access only for dependency installation

## Setup

```powershell
cd c:\RUAProgrammer\ARCTICORE\Polar-Logistics-AI
python -m pip install -r requirements.txt
```

## Generate Data

```powershell
python -m src.scenario_generator
```

This creates `data/scenarios/scenarios.json` and individual scenario CSV files.

## Run the Comparison

```powershell
python -m src.run_comparison
```

This compares the greedy and AI planners over all 50 scenarios and writes results to `data/results/`.

## Run the Dashboard

```powershell
python -m streamlit run dashboard/app.py
```

Open the URL shown by Streamlit, normally `http://localhost:8501`.

## Run Tests

```powershell
python -m pytest tests -q
```

## Mathematical Formulation

Decision variable:

- `x(i,j)` = quantity of cargo item `i` allocated to trip `j`

Constraints:

- Demand: `sum_j x(i,j) <= demanded_quantity(i)`
- Weight: `sum_i unit_weight(i) * x(i,j) <= trip_weight_capacity(j)`
- Volume: `sum_i unit_volume(i) * x(i,j) <= trip_volume_capacity(j)`

Objective:

`maximize sum_i priority_weight(i) * sum_j x(i,j) - critical_penalty * unmet_critical(i)`

Default priority weights are Critical 5, High 4, Medium 2 and Low 1.

## Algorithm Explanation

### Greedy baseline

The baseline ranks cargo by priority and allocates the largest feasible quantity to available trips. It is the mandatory reproducible benchmark.

### AI planner

The AI planner uses:

- Priority and critical-demand scoring
- Weight-density and volume-density scoring
- Bounded beam search
- Residual-capacity objective evaluation
- Distribution across trips
- State deduplication

Exhaustive A* is not used because the search state space grows combinatorially with hundreds of cargo items.

## Metrics

- Priority fulfilment = delivered weighted quantity / demanded weighted quantity
- Weight utilization = transported weight / total trip weight capacity
- Volume utilization = transported volume / total trip volume capacity
- Unmet critical demand = demanded critical quantity - delivered critical quantity

## Viva Explanation

The system demonstrates a goal-based intelligent agent: it represents allocations as states, uses a heuristic utility function, applies bounded search, and measures plan quality with explicit performance metrics. It is explainable because every cargo allocation can be traced to priority, criticality and residual capacity.

Trip loading order is not a geographical route. It is a deployment/loading sequence, with Critical and High priority cargo addressed earlier and dependency-based customization available for future manifest extensions.

## Project Structure

```text
data/scenarios/
data/results/
src/
dashboard/app.py
tests/
reports/
requirements.txt
README.md
```
