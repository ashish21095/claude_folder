"""
PDF Builder
Converts plain-text resume (with ALL CAPS section headers and bullet points)
into a clean, ATS-friendly PDF using ReportLab.
"""

import re
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import ParagraphStyle


# ── Styles ────────────────────────────────────────────────────────────────────

def _styles():
    return {
        "name": ParagraphStyle(
            "name",
            fontName="Helvetica-Bold", fontSize=15,
            alignment=TA_CENTER, spaceAfter=2,
        ),
        "contact": ParagraphStyle(
            "contact",
            fontName="Helvetica", fontSize=9,
            alignment=TA_CENTER, spaceAfter=4, textColor=colors.HexColor("#444444"),
        ),
        "section": ParagraphStyle(
            "section",
            fontName="Helvetica-Bold", fontSize=10.5,
            spaceBefore=8, spaceAfter=1,
            textColor=colors.HexColor("#1a1a2e"),
        ),
        "job_title": ParagraphStyle(
            "job_title",
            fontName="Helvetica-Bold", fontSize=10,
            spaceAfter=1,
        ),
        "normal": ParagraphStyle(
            "normal",
            fontName="Helvetica", fontSize=9.5,
            leading=14, spaceAfter=1,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Helvetica", fontSize=9.5,
            leading=14, spaceAfter=1,
            leftIndent=12, firstLineIndent=-6,  # hanging indent
        ),
    }


# ── Section header detection ──────────────────────────────────────────────────

_SECTION_RE = re.compile(r'^[A-Z][A-Z\s/&,()]+$')
_DASH_RE     = re.compile(r'^[-]{3,}$')


def _is_section_header(line: str) -> bool:
    stripped = line.strip()
    return bool(
        stripped
        and len(stripped) >= 4
        and _SECTION_RE.match(stripped)
        and stripped not in ("I", "A", "AND", "OR", "IN", "OF")
    )


# ── Builder ───────────────────────────────────────────────────────────────────

def build_resume_pdf(resume_text: str) -> bytes:
    """
    Parse resume plain text and produce ATS-friendly PDF bytes.
    Expected format from Groq:
      - First 1-3 lines: name + contact info
      - Section headers: ALL CAPS (optionally followed by a line of dashes)
      - Bullet points: lines starting with "• " or "- "
      - Job title lines: "JOB TITLE | Company | Date"
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )

    s = _styles()
    story = []
    lines = resume_text.strip().splitlines()

    header_done = False  # flip to True after we hit the first section header
    i = 0

    while i < len(lines):
        raw  = lines[i]
        line = raw.strip()
        i += 1

        if not line:
            story.append(Spacer(1, 3))
            continue

        # Skip pure dash separator lines anywhere
        if _DASH_RE.match(line):
            continue

        # ── Section header ──
        if _is_section_header(line):
            header_done = True
            story.append(Paragraph(line, s["section"]))
            story.append(HRFlowable(
                width="100%", thickness=0.6,
                color=colors.HexColor("#1a1a2e"), spaceAfter=3,
            ))
            continue

        # ── Header block (name + contact) ──
        if not header_done:
            style = s["name"] if i == 1 else s["contact"]
            story.append(Paragraph(_xml(line), style))
            continue

        # ── Bullet point ──
        if line.startswith("•") or line.startswith("-"):
            # Normalise to bullet char
            text = line.lstrip("•- ").strip()
            story.append(Paragraph(f"• {_xml(text)}", s["bullet"]))
            continue

        # ── Job title / company line (contains " | ") ──
        if " | " in line:
            story.append(Paragraph(_xml(line), s["job_title"]))
            continue

        # ── Regular text ──
        story.append(Paragraph(_xml(line), s["normal"]))

    doc.build(story)
    return buffer.getvalue()


def _xml(text: str) -> str:
    """Escape chars that break ReportLab's XML parser."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
