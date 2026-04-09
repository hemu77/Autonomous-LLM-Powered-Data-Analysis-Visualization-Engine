from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image as RLImage
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _escape(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _img_to_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


class ReportExporter:
    def __init__(self, out_dir: str):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir = self.out_dir / "plots"
        self.plots_dir.mkdir(parents=True, exist_ok=True)

    def save_plot_png(self, plot_obj: Any, filename: str, width: int = 11.5, height: int = 6.5, dpi: int = 180) -> Path:
        path = self.plots_dir / filename
        plot_obj.save(path, width=width, height=height, dpi=dpi, verbose=False)
        return path

    def export_html(
        self,
        *,
        title: str,
        dataset_profile: dict[str, Any],
        sections: list[dict[str, Any]],
        out_name: str = "report.html",
    ) -> Path:
        html_path = self.out_dir / out_name
        css = """
body { font-family: Georgia, "Times New Roman", serif; margin: 0; color: #172033; background: linear-gradient(180deg, #f3f7fb 0%, #ffffff 28%); }
.page { max-width: 1180px; margin: 0 auto; padding: 32px 28px 48px; }
h1 { margin-bottom: 6px; color: #0f172a; letter-spacing: -0.02em; }
h2 { margin-top: 28px; border-bottom: 1px solid #d6dee8; padding-bottom: 8px; color: #132238; }
.meta { color: #4c5d73; font-size: 13px; margin-bottom: 18px; }
.hero { padding: 20px 22px; border: 1px solid #d6dee8; border-radius: 16px; background: radial-gradient(circle at top right, #dff3ef 0, transparent 28%), #ffffff; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }
.card { border: 1px solid #d6dee8; background: white; padding: 16px; border-radius: 14px; margin: 14px 0; box-shadow: 0 6px 18px rgba(15,23,42,0.05);}
table { border-collapse: collapse; width: 100%; margin: 10px 0; background: #fff; }
th, td { border: 1px solid #d6dee8; padding: 8px; font-size: 12px; }
th { background: #f4f8fb; text-align: left; }
img { max-width: 100%; border: 1px solid #d6dee8; border-radius: 12px; background: #fff; }
ul { line-height: 1.55; }
"""

        def profile_table(profile: dict[str, Any]) -> str:
            rows = ["<table>", "<tr><th>Column</th><th>Dtype</th><th>Missing%</th><th>Unique</th><th>Preview</th></tr>"]
            for col in profile.get("columns", []):
                if "numeric" in col:
                    numeric = col["numeric"]
                    preview = f"mean={numeric.get('mean')}, min={numeric.get('min')}, max={numeric.get('max')}"
                elif "datetime" in col:
                    dt = col["datetime"]
                    preview = f"min={dt.get('min')}, max={dt.get('max')}"
                else:
                    tv = col.get("top_values", [])[:6]
                    preview = ", ".join([f"{x['value']}({x['count']})" for x in tv])
                rows.append(
                    "<tr>"
                    f"<td>{_escape(col['name'])}</td>"
                    f"<td>{_escape(col['dtype'])}</td>"
                    f"<td>{col['missing_pct']}</td>"
                    f"<td>{col['unique']}</td>"
                    f"<td>{_escape(preview)}</td>"
                    "</tr>"
                )
            rows.append("</table>")
            return "\n".join(rows)

        lines = [f"<html><head><meta charset='utf-8'><style>{css}</style></head><body><div class='page'>"]
        lines.append("<div class='hero'>")
        lines.append(f"<h1>{_escape(title)}</h1>")
        lines.append(
            "<div class='meta'>"
            f"Rows: {dataset_profile['shape'][0]} | Columns: {dataset_profile['shape'][1]}"
            f" | Generated UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
            "</div>"
        )
        lines.append("</div>")
        lines.append("<h2>Dataset Profile</h2>")
        lines.append(f"<div class='card'>{profile_table(dataset_profile)}</div>")

        for section in sections:
            lines.append(f"<h2>{_escape(section.get('heading', 'Section'))}</h2>")
            lines.append("<div class='card'>")
            question = section.get("question")
            if question:
                lines.append(f"<b>Question/Goal:</b> {_escape(question)}<br><br>")

            bullets = section.get("answer_bullets")
            if bullets:
                lines.append("<b>Answer:</b><ul>")
                for bullet in bullets:
                    lines.append(f"<li>{_escape(bullet)}</li>")
                lines.append("</ul>")

            table = section.get("table")
            if isinstance(table, pd.DataFrame) and not table.empty:
                lines.append("<b>Computed Table:</b>")
                lines.append(table.head(25).to_html(index=False, escape=True))

            plot_path = section.get("plot_path")
            if plot_path:
                path = Path(plot_path)
                if path.exists():
                    lines.append("<b>Plot:</b><br>")
                    lines.append(f"<img src='data:image/png;base64,{_img_to_b64(path)}' />")
                captions = section.get("caption_bullets")
                if captions:
                    lines.append("<b>Plot Insights:</b><ul>")
                    for bullet in captions:
                        lines.append(f"<li>{_escape(bullet)}</li>")
                    lines.append("</ul>")
            lines.append("</div>")

        lines.append("</div></body></html>")
        html_path.write_text("\n".join(lines), encoding="utf-8")
        return html_path

    def export_pdf(
        self,
        *,
        title: str,
        dataset_profile: dict[str, Any],
        sections: list[dict[str, Any]],
        out_name: str = "report.pdf",
    ) -> Path:
        pdf_path = self.out_dir / out_name
        styles = getSampleStyleSheet()
        story: list[Any] = []

        story.append(Paragraph(title, styles["Title"]))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Rows: {dataset_profile['shape'][0]} | Columns: {dataset_profile['shape'][1]}", styles["Normal"]))
        story.append(Spacer(1, 16))
        story.append(Paragraph("Dataset Profile", styles["Heading2"]))
        story.append(Spacer(1, 8))

        profile_rows = [["Column", "Dtype", "Missing%", "Unique", "Preview"]]
        for col in dataset_profile.get("columns", [])[:60]:
            if "numeric" in col:
                n = col["numeric"]
                preview = f"mean={n.get('mean')}, min={n.get('min')}, max={n.get('max')}"
            elif "datetime" in col:
                d = col["datetime"]
                preview = f"min={d.get('min')}, max={d.get('max')}"
            else:
                tv = col.get("top_values", [])[:5]
                preview = ", ".join([f"{x['value']}({x['count']})" for x in tv])
            profile_rows.append([col["name"], col["dtype"], str(col["missing_pct"]), str(col["unique"]), preview])

        table = Table(profile_rows, colWidths=[110, 85, 60, 50, 230])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(table)
        story.append(PageBreak())

        def safe(text: Any) -> str:
            return _escape(text)

        for section in sections:
            story.append(Paragraph(safe(section.get("heading", "Section")), styles["Heading2"]))
            story.append(Spacer(1, 6))
            if section.get("question"):
                story.append(Paragraph(f"<b>Question/Goal:</b> {safe(section['question'])}", styles["Normal"]))
                story.append(Spacer(1, 6))
            for bullet in section.get("answer_bullets", []):
                story.append(Paragraph(f"- {safe(bullet)}", styles["Normal"]))
            if section.get("answer_bullets"):
                story.append(Spacer(1, 8))

            table_df = section.get("table")
            if isinstance(table_df, pd.DataFrame) and not table_df.empty:
                rows = [list(table_df.head(25).columns)] + table_df.head(25).astype(str).values.tolist()
                t = Table(rows)
                t.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                story.append(t)
                story.append(Spacer(1, 8))

            plot_path = section.get("plot_path")
            if plot_path and Path(plot_path).exists():
                image = RLImage(str(plot_path))
                image.drawWidth = 520
                image.drawHeight = 320
                story.append(image)
                story.append(Spacer(1, 8))
            for bullet in section.get("caption_bullets", []):
                story.append(Paragraph(f"- {safe(bullet)}", styles["Normal"]))
            story.append(PageBreak())

        document = SimpleDocTemplate(str(pdf_path), pagesize=letter)
        document.build(story)
        return pdf_path

    def export_executive_summary(
        self,
        *,
        dataset_profile: dict[str, Any],
        sections: list[dict[str, Any]],
        out_name: str = "executive_summary.md",
    ) -> Path:
        path = self.out_dir / out_name
        lines = [
            "# Executive Summary",
            "",
            f"- Dataset rows: **{dataset_profile['shape'][0]}**",
            f"- Dataset columns: **{dataset_profile['shape'][1]}**",
            "",
            "## Key Findings",
        ]
        finding_count = 0
        for section in sections:
            for bullet in section.get("answer_bullets", [])[:3]:
                lines.append(f"- {bullet}")
                finding_count += 1
            for bullet in section.get("caption_bullets", [])[:3]:
                lines.append(f"- {bullet}")
                finding_count += 1
            if finding_count >= 12:
                break
        if finding_count == 0:
            lines.append("- Not enough evidence generated in this run.")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def export_technical_appendix(
        self,
        *,
        config_summary: dict[str, Any],
        benchmark_summary: dict[str, Any],
        out_name: str = "technical_appendix.md",
    ) -> Path:
        path = self.out_dir / out_name
        lines = [
            "# Technical Appendix",
            "",
            "## Pipeline Configuration",
            "```json",
            json.dumps(config_summary, indent=2),
            "```",
            "",
            "## Benchmark Summary",
            "```json",
            json.dumps(benchmark_summary, indent=2),
            "```",
            "",
            "## Guardrails",
            "- Deterministic execution for all computed tables.",
            "- JSON schema validation for analysis and plot plans.",
            "- Critic pass enabled for factuality verification.",
            "- Narrative bullets should be grounded in computed evidence.",
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path
