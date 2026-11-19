from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from .cargo_model import CargoItem, Scenario, Trip


CATEGORIES = [
    "Food & Water",
    "Medical Supplies",
    "Fuel & Lubricants",
    "Scientific Equipment",
    "Research Samples",
    "Personal Protective Equipment",
    "Communication Equipment",
    "Spare Parts",
    "Shelter & Heating",
]

ITEM_NAMES = {
    "Food & Water": ["Field ration packs", "Drinking water", "Preserved vegetables", "Protein bars"],
    "Medical Supplies": ["Emergency medicine", "First-aid kits", "Antifreeze treatment", "Diagnostic kits"],
    "Fuel & Lubricants": ["Generator fuel", "Vehicle lubricant", "Heating fuel", "Fuel filters"],
    "Scientific Equipment": ["Ice cores", "Weather sensors", "Seismometers", "Spectrometer parts"],
    "Research Samples": ["Sample containers", "Cryogenic storage", "Preservation media", "Specimen cases"],
    "Personal Protective Equipment": ["Thermal suits", "Insulated boots", "Safety gloves", "Protective goggles"],
    "Communication Equipment": ["Satellite terminals", "Radio batteries", "Antenna modules", "Data relays"],
    "Spare Parts": ["Generator parts", "Vehicle parts", "Pump assemblies", "Tool kits"],
    "Shelter & Heating": ["Insulation panels", "Space heaters", "Tent components", "Emergency blankets"],
}

PRIORITIES = ("Low", "Medium", "High", "Critical")


def generate_scenario(
    scenario_index: int,
    seed: int,
    cargo_count: int = 200,
    trip_count: int = 4,
    capacity_scale: float = 1.0,
) -> Scenario:
    if cargo_count < 1:
        raise ValueError("cargo_count must be positive")
    if trip_count < 1:
        raise ValueError("trip_count must be positive")
    if capacity_scale <= 0:
        raise ValueError("capacity_scale must be positive")

    rng = random.Random(seed)
    trips = []

    for trip_number in range(1, trip_count + 1):
        trips.append(Trip(
            trip_id=f"TRIP-{trip_number:02d}",
            maximum_weight=round(rng.uniform(600.0, 950.0) * capacity_scale, 2),
            maximum_volume=round(rng.uniform(18.0, 32.0) * capacity_scale, 2),
        ))

    cargo_items = []
    for cargo_number in range(1, cargo_count + 1):
        category = rng.choice(CATEGORIES)
        priority_roll = rng.random()
        if priority_roll < 0.08:
            priority = "Critical"
            critical_flag = True
        elif priority_roll < 0.27:
            priority = "High"
            critical_flag = rng.random() < 0.35
        elif priority_roll < 0.62:
            priority = "Medium"
            critical_flag = rng.random() < 0.10
        else:
            priority = "Low"
            critical_flag = False

        unit_weight = round(rng.uniform(0.3, 28.0), 3)
        unit_volume = round(rng.uniform(0.005, 1.20), 4)
        quantity = rng.randint(1, 50)

        cargo_items.append(CargoItem(
            cargo_id=f"CARGO-{cargo_number:04d}",
            cargo_name=rng.choice(ITEM_NAMES[category]),
            category=category,
            quantity=quantity,
            unit_weight=unit_weight,
            unit_volume=unit_volume,
            priority=priority,
            critical_flag=critical_flag,
        ))

    scenario = Scenario(
        scenario_id=f"SCENARIO-{scenario_index:03d}",
        seed=seed,
        cargo_items=cargo_items,
        trips=trips,
    )
    scenario.validate()
    return scenario


def generate_scenarios(
    count: int = 50,
    base_seed: int = 26062,
    cargo_count: int = 200,
    trip_count: int = 4,
    capacity_scale: float = 1.0,
) -> list[Scenario]:
    if count < 1:
        raise ValueError("count must be positive")

    return [
        generate_scenario(
            scenario_index=index,
            seed=base_seed + index - 1,
            cargo_count=cargo_count,
            trip_count=trip_count,
            capacity_scale=capacity_scale,
        )
        for index in range(1, count + 1)
    ]


def save_scenarios(scenarios: list[Scenario], directory: str | Path) -> tuple[Path, list[Path]]:
    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    combined_path = output_dir / "scenarios.json"
    combined_path.write_text(
        json.dumps([scenario.to_dict() for scenario in scenarios], indent=2),
        encoding="utf-8",
    )

    csv_paths = []
    for scenario in scenarios:
        cargo_path = output_dir / f"{scenario.scenario_id.lower()}_cargo.csv"
        with cargo_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=[
                "cargo_id", "cargo_name", "category", "quantity",
                "unit_weight", "unit_volume", "priority", "critical_flag",
            ])
            writer.writeheader()
            for item in scenario.cargo_items:
                writer.writerow({
                    "cargo_id": item.cargo_id,
                    "cargo_name": item.cargo_name,
                    "category": item.category,
                    "quantity": item.quantity,
                    "unit_weight": item.unit_weight,
                    "unit_volume": item.unit_volume,
                    "priority": item.priority,
                    "critical_flag": item.critical_flag,
                })

        trip_path = output_dir / f"{scenario.scenario_id.lower()}_trips.csv"
        with trip_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["trip_id", "maximum_weight", "maximum_volume"])
            writer.writeheader()
            for trip in scenario.trips:
                writer.writerow({
                    "trip_id": trip.trip_id,
                    "maximum_weight": trip.maximum_weight,
                    "maximum_volume": trip.maximum_volume,
                })

        csv_paths.extend([cargo_path, trip_path])

    return combined_path, csv_paths


def load_scenarios_json(path: str | Path) -> list[Scenario]:
    from .cargo_model import scenario_from_dict

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [scenario_from_dict(scenario_data) for scenario_data in data]


if __name__ == "__main__":
    scenarios = generate_scenarios(count=50, base_seed=26062, cargo_count=200, trip_count=4)
    combined_path, _ = save_scenarios(scenarios, Path(__file__).resolve().parents[1] / "data" / "scenarios")
    print(f"Generated {len(scenarios)} scenarios")
    print(combined_path)
