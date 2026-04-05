"""
PDF Builder
Merges BASE_RESUME with Groq tailoring edits and renders an ATS-friendly PDF
styled to match the candidate's template (blue headers, skills table, etc.).
"""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.lib.styles import ParagraphStyle
from config import BASE_RESUME

# ── Brand colours (matching the template) ─────────────────────────────────────
DARK_BLUE  = colors.HexColor("#1B3A6B")
MID_BLUE   = colors.HexColor("#2E6DA4")
LIGHT_GREY = colors.HexColor("#F4F6F9")
RULE_GREY  = colors.HexColor("#CCCCCC")

PAGE_W, PAGE_H = A4
LM = RM = 18 * mm
TM = BM = 14 * mm

# ── Styles ─────────────────────────────────────────────────────────────────────

def _s():
    return {
        "name":       ParagraphStyle("name",    fontName="Helvetica-Bold", fontSize=18,
                                     alignment=TA_CENTER, textColor=DARK_BLUE, spaceAfter=2),
        "subtitle":   ParagraphStyle("sub",     fontName="Helvetica",      fontSize=10,
                                     alignment=TA_CENTER, textColor=MID_BLUE,  spaceAfter=3),
        "contact":    ParagraphStyle("contact", fontName="Helvetica",      fontSize=8.5,
                                     alignment=TA_CENTER, textColor=colors.HexColor("#444444"), spaceAfter=4),
        "badge":      ParagraphStyle("badge",   fontName="Helvetica-Bold", fontSize=8,
                                     alignment=TA_CENTER, textColor=MID_BLUE),
        "sec_head":   ParagraphStyle("sh",      fontName="Helvetica-Bold", fontSize=10.5,
                                     textColor=DARK_BLUE, spaceBefore=8, spaceAfter=1),
        "summary":    ParagraphStyle("summ",    fontName="Helvetica",      fontSize=9.5,
                                     leading=14, spaceAfter=2),
        "corestack":  ParagraphStyle("cs",      fontName="Helvetica-Oblique", fontSize=8.5,
                                     textColor=colors.HexColor("#555555"), spaceAfter=2, leading=13),
        "role":       ParagraphStyle("role",    fontName="Helvetica-Bold", fontSize=9.5,
                                     textColor=MID_BLUE,  spaceAfter=1),
        "rolemeta":   ParagraphStyle("rm",      fontName="Helvetica-Oblique", fontSize=8.5,
                                     textColor=colors.HexColor("#555555"), spaceAfter=2),
        "bullet":     ParagraphStyle("bul",     fontName="Helvetica",      fontSize=9,
                                     leading=13, spaceAfter=1, leftIndent=10, firstLineIndent=-6),
        "skill_cat":  ParagraphStyle("scat",    fontName="Helvetica-Bold", fontSize=9,
                                     textColor=MID_BLUE,  leading=13),
        "skill_val":  ParagraphStyle("sval",    fontName="Helvetica",      fontSize=9,  leading=13),
        "cert":       ParagraphStyle("cert",    fontName="Helvetica",      fontSize=9,  leading=14),
        "edu_title":  ParagraphStyle("et",      fontName="Helvetica-Bold", fontSize=9.5),
        "edu_sub":    ParagraphStyle("es",      fontName="Helvetica",      fontSize=9,
                                     textColor=colors.HexColor("#555555")),
        "normal":     ParagraphStyle("norm",    fontName="Helvetica",      fontSize=9,  leading=13),
    }


def _x(t: str) -> str:
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _section(label: str, s: dict, story: list):
    story.append(Paragraph(_x(label), s["sec_head"]))
    story.append(HRFlowable(width="100%", thickness=0.75, color=DARK_BLUE, spaceAfter=4))


# ── Parse BASE_RESUME into sections ───────────────────────────────────────────

def _parse_base() -> dict:
    """Return a dict of named sections from BASE_RESUME."""
    sections = {
        "name": "", "subtitle": "", "contact": "", "badges": [],
        "summary": "", "corestack": "",
        "roles": [],          # list of {title, company, dates, location, bullets}
        "skills": [],         # list of {category, value}
        "certs": [],          # list of strings
        "education": [],      # list of {degree, school, dates}
    }

    current_role = None
    in_skills = False
    in_summary = False
    in_certs = False
    in_edu = False
    in_work = False
    header_lines = []

    for raw in BASE_RESUME.strip().splitlines():
        line = raw.strip()
        if not line:
            continue

        # ── Header block ──
        if line == "HEADER":
            continue
        if line.startswith("CERTIFICATIONS_BADGES:"):
            sections["badges"] = [b.strip() for b in line.split(":", 1)[1].split("|")]
            continue

        # ── Section markers ──
        if line == "PROFESSIONAL SUMMARY":
            in_summary = True; in_skills = in_certs = in_edu = in_work = False
            continue
        if line == "WORK EXPERIENCE":
            in_work = True; in_summary = in_skills = in_certs = in_edu = False
            continue
        if line == "TECHNICAL SKILLS":
            in_skills = True; in_summary = in_work = in_certs = in_edu = False
            if current_role: sections["roles"].append(current_role); current_role = None
            continue
        if line == "CERTIFICATIONS":
            in_certs = True; in_summary = in_work = in_skills = in_edu = False
            continue
        if line == "EDUCATION":
            in_edu = True; in_summary = in_work = in_skills = in_certs = False
            continue

        # ── Collect header (name/subtitle/contact) ──
        if not in_summary and not in_work and not in_skills and not in_certs and not in_edu:
            header_lines.append(line)
            continue

        # ── Summary ──
        if in_summary:
            if line.startswith("Core stack:"):
                sections["corestack"] = line
            else:
                sections["summary"] += (" " if sections["summary"] else "") + line
            continue

        # ── Work experience ──
        if in_work:
            if "|" in line and not line.startswith("•"):
                if current_role:
                    sections["roles"].append(current_role)
                parts = [p.strip() for p in line.split("|")]
                current_role = {
                    "title":    parts[0] if len(parts) > 0 else "",
                    "company":  parts[1] if len(parts) > 1 else "",
                    "dates":    parts[2] if len(parts) > 2 else "",
                    "location": parts[3] if len(parts) > 3 else "",
                    "bullets":  [],
                }
            elif line.startswith("•") and current_role:
                current_role["bullets"].append(line)
            continue

        # ── Skills ──
        if in_skills:
            if "|" in line:
                cat, _, val = line.partition("|")
                sections["skills"].append({"category": cat.strip(), "value": val.strip()})
            continue

        # ── Certifications ──
        if in_certs:
            sections["certs"].append(line)
            continue

        # ── Education ──
        if in_edu:
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                sections["education"].append({
                    "degree": parts[0], "school": parts[1] if len(parts) > 1 else "",
                    "dates":  parts[2] if len(parts) > 2 else "",
                })
            continue

    if current_role:
        sections["roles"].append(current_role)

    # Assign header lines
    if header_lines:
        sections["name"]     = header_lines[0] if len(header_lines) > 0 else ""
        sections["subtitle"] = header_lines[1] if len(header_lines) > 1 else ""
        sections["contact"]  = header_lines[2] if len(header_lines) > 2 else ""

    return sections


# ── Apply Groq edits ───────────────────────────────────────────────────────────

def _apply_edits(sections: dict, edits: dict) -> dict:
    """Merge Groq tailoring edits into the parsed sections."""
    if not edits:
        return sections

    # Update summary
    if edits.get("summary"):
        sections["summary"] = edits["summary"]
        sections["corestack"] = ""  # will be re-added if needed

    # Prepend new Workday bullets (first role = Workday)
    new_bullets = edits.get("workday_bullets", [])
    if new_bullets and sections["roles"]:
        # Normalise bullet format
        normalised = []
        for b in new_bullets:
            b = b.strip()
            if not b.startswith("•"):
                b = "• " + b.lstrip("-• ")
            normalised.append(b)
        # Insert after existing bullets (keep existing, add new at end)
        sections["roles"][0]["bullets"].extend(normalised)

    # Update skill categories
    skill_updates = edits.get("skills_updates", {})
    for skill in sections["skills"]:
        if skill["category"] in skill_updates:
            skill["value"] = skill_updates[skill["category"]]
    # Add new categories not already present
    existing_cats = {s["category"] for s in sections["skills"]}
    for cat, val in skill_updates.items():
        if cat not in existing_cats:
            sections["skills"].append({"category": cat, "value": val})

    return sections


# ── PDF renderer ───────────────────────────────────────────────────────────────

def build_resume_pdf(edits: dict) -> bytes:
    """Build a styled PDF from BASE_RESUME merged with Groq edits."""
    sections = _apply_edits(_parse_base(), edits)
    s = _s()
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
    )
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph(_x(sections["name"]), s["name"]))
    if sections["subtitle"]:
        story.append(Paragraph(_x(sections["subtitle"]), s["subtitle"]))
    if sections["contact"]:
        story.append(Paragraph(_x(sections["contact"]), s["contact"]))

    # Certification badges row
    if sections["badges"]:
        badge_data = [[Paragraph(_x(b), s["badge"]) for b in sections["badges"]]]
        badge_table = Table(badge_data, colWidths=[(PAGE_W - LM - RM) / len(sections["badges"])] * len(sections["badges"]))
        badge_table.setStyle(TableStyle([
            ("BOX",         (0, 0), (-1, -1), 0.5, MID_BLUE),
            ("INNERGRID",   (0, 0), (-1, -1), 0.5, MID_BLUE),
            ("BACKGROUND",  (0, 0), (-1, -1), LIGHT_GREY),
            ("TOPPADDING",  (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ]))
        story.append(badge_table)
        story.append(Spacer(1, 4))

    # ── Professional Summary ──────────────────────────────────────────────────
    _section("PROFESSIONAL SUMMARY", s, story)
    if sections["summary"]:
        story.append(Paragraph(_x(sections["summary"]), s["summary"]))
    if sections["corestack"]:
        story.append(Paragraph(_x(sections["corestack"]), s["corestack"]))

    # ── Work Experience ───────────────────────────────────────────────────────
    _section("WORK EXPERIENCE", s, story)
    for role in sections["roles"]:
        # Role title + company row
        title_cell = Paragraph(f'<font color="{MID_BLUE.hexval()}">{_x(role["title"].title())}</font> · <font color="{MID_BLUE.hexval()}">{_x(role["company"])}</font>', s["role"])
        meta_cell  = Paragraph(_x(f'{role["location"]}  |  {role["dates"]}'), s["rolemeta"])
        role_table = Table([[title_cell, meta_cell]], colWidths=[
            (PAGE_W - LM - RM) * 0.62,
            (PAGE_W - LM - RM) * 0.38,
        ])
        role_table.setStyle(TableStyle([
            ("VALIGN",       (0, 0), (-1, -1), "BOTTOM"),
            ("ALIGN",        (1, 0), (1, 0),   "RIGHT"),
            ("TOPPADDING",   (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
        ]))
        story.append(role_table)
        story.append(HRFlowable(width="100%", thickness=0.4, color=RULE_GREY, spaceAfter=2))
        for bullet in role["bullets"]:
            text = bullet.lstrip("• ").strip()
            story.append(Paragraph(f"▸  {_x(text)}", s["bullet"]))
        story.append(Spacer(1, 4))

    # ── Technical Skills ──────────────────────────────────────────────────────
    _section("TECHNICAL SKILLS", s, story)
    skill_rows = []
    for sk in sections["skills"]:
        skill_rows.append([
            Paragraph(_x(sk["category"]), s["skill_cat"]),
            Paragraph(_x(sk["value"]),    s["skill_val"]),
        ])
    if skill_rows:
        col1 = (PAGE_W - LM - RM) * 0.18
        col2 = (PAGE_W - LM - RM) * 0.82
        skill_table = Table(skill_rows, colWidths=[col1, col2])
        skill_table.setStyle(TableStyle([
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",   (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS",(0, 0), (-1, -1), [colors.white, LIGHT_GREY]),
            ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ]))
        story.append(skill_table)

    # ── Certifications ────────────────────────────────────────────────────────
    _section("CERTIFICATIONS", s, story)
    for cert in sections["certs"]:
        parts = cert.split(" — ", 1)
        if len(parts) == 2:
            story.append(Paragraph(
                f'<b>{_x(parts[0])}</b>  —  <font color="#555555">{_x(parts[1])}</font>',
                s["cert"]
            ))
        else:
            story.append(Paragraph(_x(cert), s["cert"]))

    # ── Education ─────────────────────────────────────────────────────────────
    _section("EDUCATION", s, story)
    for edu in sections["education"]:
        story.append(Paragraph(_x(edu["degree"]), s["edu_title"]))
        story.append(Paragraph(
            _x(f'{edu["school"]}    {edu["dates"]}'), s["edu_sub"]
        ))

    doc.build(story)
    return buffer.getvalue()
