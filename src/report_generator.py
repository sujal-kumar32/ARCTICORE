from __future__ import annotations

import csv
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def save_csv_report(rows: list[dict], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output.write_text("", encoding="utf-8")
        return output

    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return output


def save_json_report(rows: list[dict], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return output


def generate_pdf_report(rows: list[dict], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    document = SimpleDocTemplate(str(output), pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Integrated Polar Expedition Logistics and Asset Management System", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Smart India Hackathon 2026 - PS ID: SIH26062", styles["Heading2"]),
        Paragraph(
            "Synthetic experimental report. The generated cargo manifests are not official MoES records.",
            styles["BodyText"],
        ),
        Spacer(1, 12),
    ]

    if rows:
        numeric_columns = [
            "greedy_priority_weighted_fulfilment",
            "ai_priority_weighted_fulfilment",
            "greedy_weight_utilization",
            "ai_weight_utilization",
            "greedy_volume_utilization",
            "ai_volume_utilization",
            "greedy_unmet_critical_demand",
            "ai_unmet_critical_demand",
        ]

        averages = {}
        for column in numeric_columns:
            averages[column] = sum(row[column] for row in rows) / len(rows)

        story.append(Paragraph("Aggregate Results", styles["Heading2"]))
        summary_data = [["Metric", "Greedy", "AI Planner"]]
        summary_data.append(["Priority fulfilment (%)", f"{averages['greedy_priority_weighted_fulfilment']:.2f}", f"{averages['ai_priority_weighted_fulfilment']:.2f}"])
        summary_data.append(["Weight utilization (%)", f"{averages['greedy_weight_utilization']:.2f}", f"{averages['ai_weight_utilization']:.2f}"])
        summary_data.append(["Volume utilization (%)", f"{averages['greedy_volume_utilization']:.2f}", f"{averages['ai_volume_utilization']:.2f}"])
        summary_data.append(["Unmet critical demand", f"{averages['greedy_unmet_critical_demand']:.2f}", f"{averages['ai_unmet_critical_demand']:.2f}"])

        summary_table = Table(summary_data, repeatRows=1)
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12355B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ]))
        story.extend([summary_table, Spacer(1, 18), PageBreak()])

        story.append(Paragraph("Scenario-Level Results", styles["Heading2"]))
        table_data = [["Scenario", "Greedy %", "AI %", "Greedy Weight %", "AI Weight %", "Greedy Unmet", "AI Unmet"]]
        for row in rows:
            table_data.append([
                row["scenario_id"],
                f"{row['greedy_priority_weighted_fulfilment']:.2f}",
                f"{row['ai_priority_weighted_fulfilment']:.2f}",
                f"{row['greedy_weight_utilization']:.2f}",
                f"{row['ai_weight_utilization']:.2f}",
                str(row["greedy_unmet_critical_demand"]),
                str(row["ai_unmet_critical_demand"]),
            ])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12355B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
        ]))
        story.append(table)

    document.build(story)
    return output
