"""
Professional PDF CV Generator using ReportLab.
Creates high-quality, ATS-friendly PDFs with premium design.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
import os


# Register DejaVu fonts (available in the system) with better names
FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', FONT_DIR + 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', FONT_DIR + 'DejaVuSans-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSerif', FONT_DIR + 'DejaVuSerif.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSerif-Bold', FONT_DIR + 'DejaVuSerif-Bold.ttf'))
    FONT_BODY = 'DejaVuSans'
    FONT_BODY_BOLD = 'DejaVuSans-Bold'
    FONT_HEADING = 'DejaVuSerif'
    FONT_HEADING_BOLD = 'DejaVuSerif-Bold'
except:
    FONT_BODY = 'Helvetica'
    FONT_BODY_BOLD = 'Helvetica-Bold'
    FONT_HEADING = 'Helvetica'
    FONT_HEADING_BOLD = 'Helvetica-Bold'


# Colors
COLOR_PRIMARY = HexColor('#1a1a2e')
COLOR_ACCENT = HexColor('#4f46e5')
COLOR_ACCENT_LIGHT = HexColor('#818cf8')
COLOR_TEXT = HexColor('#1e293b')
COLOR_TEXT_LIGHT = HexColor('#64748b')
COLOR_BG = HexColor('#f8fafc')
COLOR_LINE = HexColor('#e2e8f0')
COLOR_SIDEBAR = HexColor('#f1f5f9')


class CVRenderer:
    """Renders a CV profile into a professional PDF."""

    def __init__(self, profile: dict):
        self.profile = profile
        self.width, self.height = A4
        self.margin = 20 * mm
        self.content_width = self.width - 2 * self.margin

    def render(self, output_path: str, template: str = 'modern'):
        """Render the CV to PDF."""
        c = canvas.Canvas(output_path, pagesize=A4)
        c.setTitle(self.profile.get('title', 'CV'))
        c.setAuthor(self.profile.get('email', ''))

        if template == 'modern':
            self._render_modern(c)
        elif template == 'classic':
            self._render_classic(c)
        elif template == 'minimal':
            self._render_minimal(c)
        elif template == 'ats-friendly':
            self._render_ats_friendly(c)
        else:
            self._render_modern(c)

        c.save()

    def _draw_header_modern(self, c):
        """Draw the header section for modern template."""
        # Header background
        c.setFillColor(COLOR_PRIMARY)
        c.rect(0, self.height - 55 * mm, self.width, 55 * mm, fill=1, stroke=0)

        # Accent bar at bottom of header
        c.setFillColor(COLOR_ACCENT)
        c.rect(0, self.height - 55 * mm, self.width, 2 * mm, fill=1, stroke=0)

        # Decorative gradient effect (simulated with lines)
        c.setFillColor(COLOR_ACCENT_LIGHT)
        c.setFillAlpha(0.15)
        path = c.beginPath()
        path.moveTo(self.width - 80 * mm, self.height - 55 * mm)
        path.lineTo(self.width, self.height - 55 * mm)
        path.lineTo(self.width, self.height)
        path.lineTo(self.width - 60 * mm, self.height)
        path.close()
        c.drawPath(path, fill=1, stroke=0)
        c.setFillAlpha(1)

        # Pre-title
        c.setFillColor(COLOR_ACCENT_LIGHT)
        c.setFont(FONT_BODY, 8)
        c.drawString(self.margin, self.height - 15 * mm, "CURRICULUM VITAE")

        # Name / Title
        c.setFillColor(white)
        c.setFont(FONT_HEADING_BOLD, 22)
        title = self.profile.get('title', '')
        c.drawString(self.margin, self.height - 28 * mm, title)

        # Subtitle
        c.setFont(FONT_BODY, 9)
        c.setFillColor(HexColor('#a5b4fc'))
        subtitle = self.profile.get('subtitle', '')
        c.drawString(self.margin, self.height - 35 * mm, subtitle)

        # Contact card (right side)
        card_x = self.width - self.margin - 55 * mm
        card_y = self.height - 22 * mm
        card_w = 55 * mm
        card_h = 35 * mm

        c.setFillColor(HexColor('#ffffff15'))
        c.roundRect(card_x, card_y - card_h + 5 * mm, card_w, card_h, 3 * mm, fill=1, stroke=0)

        # Contact info
        c.setFont(FONT_BODY, 7.5)
        c.setFillColor(white)
        contact_y = self.height - 26 * mm
        items = [
            (self.profile.get('email', ''), '✉'),
            (self.profile.get('location', ''), '📍'),
            (self.profile.get('linkedin', ''), '🔗'),
        ]
        for i, (text, icon) in enumerate(items):
            if text:
                c.setFillColor(HexColor('#a5b4fc'))
                c.drawString(card_x + 4 * mm, contact_y - i * 7 * mm, icon)
                c.setFillColor(white)
                c.drawString(card_x + 10 * mm, contact_y - i * 7 * mm, text[:35])

    def _render_modern(self, c):
        """Render modern template."""
        self._draw_header_modern(c)

        y = self.height - 62 * mm
        left_col_w = self.content_width * 0.62
        right_col_w = self.content_width * 0.35
        col_gap = 8 * mm

        # Left column
        left_x = self.margin
        # Right column
        right_x = self.margin + left_col_w + col_gap

        # --- Profile Section ---
        y = self._draw_section_modern(
            c, left_x, y, left_col_w,
            "01", "Professional Profile",
            [Paragraph(self.profile.get('profile', ''), self._body_style())]
        )

        y -= 5 * mm

        # --- Experience Section ---
        y = self._draw_section_modern(
            c, left_x, y, left_col_w,
            "02", "Professional Experience",
            self._render_experience_modern(c, left_x, y, left_col_w)
        )

        y -= 5 * mm

        # --- Education Section ---
        if self.profile.get('education'):
            y = self._draw_section_modern(
                c, left_x, y, left_col_w,
                "03", "Education",
                self._render_education_modern(c, left_x, y, left_col_w)
            )

        # --- Certifications ---
        if self.profile.get('certifications'):
            y = self._draw_section_modern(
                c, left_x, y, left_col_w,
                "04", "Certifications",
                self._render_certifications_modern(c, left_x, y, left_col_w)
            )

        # --- Right Sidebar ---
        sidebar_y = self.height - 62 * mm

        # Skills
        sidebar_y = self._draw_sidebar_skills(c, right_x, sidebar_y, right_col_w)

        # Languages
        if self.profile.get('languages'):
            sidebar_y = self._draw_sidebar_languages(c, right_x, sidebar_y, right_col_w)

    def _draw_section_modern(self, c, x, y, width, num, title, content_items):
        """Draw a numbered section."""
        # Section header
        c.setFont(FONT_HEADING_BOLD, 11)
        c.setFillColor(COLOR_PRIMARY)
        c.drawString(x, y, num)
        c.setFont(FONT_HEADING, 11)
        c.setFillColor(COLOR_TEXT)
        c.drawString(x + 8 * mm, y, title)

        # Underline
        c.setStrokeColor(COLOR_LINE)
        c.setLineWidth(0.5)
        c.line(x, y - 2 * mm, x + width, y - 2 * mm)

        y -= 6 * mm

        for item in content_items:
            if isinstance(item, Paragraph):
                w, h = item.wrap(width, 100 * mm)
                item.drawOn(c, x, y - h)
                y -= h + 3 * mm
            elif hasattr(item, 'drawOn'):
                item.drawOn(c, x, y)
                y -= 15 * mm

        return y

    def _render_experience_modern(self, c, x, y, width):
        """Render experience items."""
        items = []
        for job in self.profile.get('experience', []):
            # Period
            period = f"{job.get('start_date', '')} — {job.get('end_date', 'Present')}"
            p_period = Paragraph(
                f'<font color="#4f46e5" size="7.5"><b>{period.upper()}</b></font>',
                ParagraphStyle('period', fontName=FONT_BODY_BOLD, fontSize=7.5,
                             textColor=COLOR_ACCENT, spaceBefore=0, spaceAfter=1)
            )
            items.append(p_period)

            # Title
            p_title = Paragraph(
                f'<b><font size="10" color="#1a1a2e">{job.get("title", "")}</font></b>',
                ParagraphStyle('title', fontName=FONT_BODY_BOLD, fontSize=10,
                             textColor=COLOR_PRIMARY, spaceBefore=0, spaceAfter=1)
            )
            items.append(p_title)

            # Company
            p_company = Paragraph(
                f'<font size="8.5" color="#64748b">{job.get("company", "")}{" · " + job["location"] if job.get("location") else ""}</font>',
                ParagraphStyle('company', fontName=FONT_BODY, fontSize=8.5,
                             textColor=COLOR_TEXT_LIGHT, spaceBefore=0, spaceAfter=3)
            )
            items.append(p_company)

            # Description
            desc = job.get('description', '')
            if desc:
                p_desc = Paragraph(
                    f'<font size="8.5" color="#374151">{desc}</font>',
                    ParagraphStyle('desc', fontName=FONT_BODY, fontSize=8.5,
                                 textColor=COLOR_TEXT, leading=12, spaceBefore=0, spaceAfter=8)
                )
                items.append(p_desc)

        return items

    def _render_education_modern(self, c, x, y, width):
        """Render education items."""
        items = []
        for edu in self.profile.get('education', []):
            p_year = Paragraph(
                f'<font color="#64748b" size="8.5">{edu.get("year", "")}</font>',
                ParagraphStyle('year', fontName=FONT_BODY, fontSize=8.5,
                             textColor=COLOR_TEXT_LIGHT, spaceBefore=0, spaceAfter=1)
            )
            items.append(p_year)

            p_degree = Paragraph(
                f'<b><font size="9.5" color="#1a1a2e">{edu.get("degree", "")}</font></b>',
                ParagraphStyle('degree', fontName=FONT_BODY_BOLD, fontSize=9.5,
                             textColor=COLOR_PRIMARY, spaceBefore=0, spaceAfter=1)
            )
            items.append(p_degree)

            p_inst = Paragraph(
                f'<font size="8.5" color="#64748b">{edu.get("institution", "")}</font>',
                ParagraphStyle('inst', fontName=FONT_BODY, fontSize=8.5,
                             textColor=COLOR_TEXT_LIGHT, spaceBefore=0, spaceAfter=6)
            )
            items.append(p_inst)

        return items

    def _render_certifications_modern(self, c, x, y, width):
        """Render certification badges."""
        items = []
        certs = self.profile.get('certifications', [])
        # Simple paragraph with certs separated
        cert_text = ' · '.join(f'<b>{c}</b>' for c in certs)
        p = Paragraph(
            f'<font size="8.5" color="#4f46e5">{cert_text}</font>',
            ParagraphStyle('cert', fontName=FONT_BODY, fontSize=8.5,
                         textColor=COLOR_ACCENT, leading=14, spaceBefore=0, spaceAfter=0)
        )
        items.append(p)
        return items

    def _draw_sidebar_skills(self, c, x, y, width):
        """Draw skills sidebar section."""
        # Background card
        c.setFillColor(COLOR_BG)
        c.roundRect(x, y - 60 * mm, width, 55 * mm, 3 * mm, fill=1, stroke=0)
        c.setStrokeColor(COLOR_LINE)
        c.setLineWidth(0.5)
        c.roundRect(x, y - 60 * mm, width, 55 * mm, 3 * mm, fill=0, stroke=1)

        # Title
        c.setFont(FONT_BODY_BOLD, 8)
        c.setFillColor(COLOR_TEXT_LIGHT)
        c.drawString(x + 4 * mm, y - 6 * mm, "CORE COMPETENCIES")

        # Skills tags
        keywords = self.profile.get('keywords', [])
        tag_x = x + 4 * mm
        tag_y = y - 12 * mm
        line_h = 8 * mm
        max_x = x + width - 4 * mm

        for kw in keywords:
            # Estimate text width (approximate)
            text_w = len(kw) * 2.2 * mm + 4 * mm
            if tag_x + text_w > max_x:
                tag_x = x + 4 * mm
                tag_y -= line_h

            # Tag background
            c.setFillColor(HexColor('#eef2ff'))
            c.setStrokeColor(HexColor('#c7d2fe'))
            c.setLineWidth(0.3)
            c.roundRect(tag_x, tag_y - 4 * mm, text_w, 5.5 * mm, 1 * mm, fill=1, stroke=1)

            # Tag text
            c.setFont(FONT_BODY, 7)
            c.setFillColor(COLOR_ACCENT)
            c.drawString(tag_x + 2 * mm, tag_y - 2 * mm, kw[:20])

            tag_x += text_w + 2 * mm

        return y - 65 * mm

    def _draw_sidebar_languages(self, c, x, y, width):
        """Draw languages sidebar section."""
        # Title
        c.setFont(FONT_BODY_BOLD, 8)
        c.setFillColor(COLOR_TEXT_LIGHT)
        c.drawString(x + 4 * mm, y - 6 * mm, "LANGUAGES")

        y -= 12 * mm

        for lang in self.profile.get('languages', []):
            # Lang card
            c.setFillColor(white)
            c.setStrokeColor(COLOR_LINE)
            c.setLineWidth(0.3)
            c.roundRect(x + 2 * mm, y - 8 * mm, width - 4 * mm, 9 * mm, 1 * mm, fill=1, stroke=1)

            c.setFont(FONT_BODY_BOLD, 8.5)
            c.setFillColor(COLOR_TEXT)
            c.drawString(x + 5 * mm, y - 5 * mm, lang.get('name', ''))

            c.setFont(FONT_BODY, 7.5)
            c.setFillColor(COLOR_TEXT_LIGHT)
            c.drawRightString(x + width - 5 * mm, y - 5 * mm, lang.get('level', ''))

            y -= 11 * mm

        return y

    def _body_style(self):
        return ParagraphStyle(
            'body',
            fontName=FONT_BODY,
            fontSize=9.5,
            textColor=COLOR_TEXT,
            leading=14,
            spaceBefore=0,
            spaceAfter=3,
            alignment=TA_JUSTIFY
        )

    def _render_classic(self, c):
        """Classic elegant template."""
        # Header
        c.setFillColor(COLOR_PRIMARY)
        c.rect(0, self.height - 50 * mm, self.width, 50 * mm, fill=1, stroke=0)

        # Accent line
        c.setFillColor(HexColor('#7c3aed'))
        c.rect(self.margin, self.height - 51 * mm, 80 * mm, 1.5 * mm, fill=1, stroke=0)

        # Name
        c.setFont(FONT_HEADING_BOLD, 24)
        c.setFillColor(white)
        c.drawString(self.margin, self.height - 25 * mm, self.profile.get('title', ''))

        # Subtitle
        c.setFont(FONT_BODY, 9)
        c.setFillColor(HexColor('#a78bfa'))
        c.drawString(self.margin, self.height - 32 * mm, self.profile.get('subtitle', ''))

        # Contact (right)
        c.setFont(FONT_BODY, 8.5)
        c.setFillColor(HexColor('#ffffffcc'))
        contact_items = [
            self.profile.get('email', ''),
            self.profile.get('location', ''),
            self.profile.get('linkedin', '')
        ]
        contact_str = ' · '.join(c for c in contact_items if c)
        c.drawRightString(self.width - self.margin, self.height - 25 * mm, contact_str)

        y = self.height - 58 * mm
        left_w = self.content_width * 0.65
        right_x = self.margin + left_w + 8 * mm

        # Profile
        y = self._draw_section_classic(c, self.margin, y, left_w, "Profile",
                                        [self.profile.get('profile', '')])

        y -= 5 * mm

        # Experience
        if self.profile.get('experience'):
            items = []
            for job in self.profile.get('experience', []):
                period = f"{job.get('start_date', '')} - {job.get('end_date', 'Present')}"
                items.append(f"<b><font color='#1c1917'>{job.get('title', '')}</font></b>")
                items.append(f"<font color='#7c3aed'>{job.get('company', '')}{' · ' + job['location'] if job.get('location') else ''}</font>")
                items.append(f"<font size='8' color='#78716c'>{period}</font>")
                items.append(f"<font size='8.5'>{job.get('description', '')}</font>")
                items.append("---")  # paragraph separator

            y = self._draw_section_classic(c, self.margin, y, left_w, "Experience",
                                            items)

        # Education
        if self.profile.get('education'):
            edu_items = []
            for edu in self.profile.get('education', []):
                edu_items.append(f"<b>{edu.get('degree', '')}</b>")
                edu_items.append(f"<font color='#78716c'>{edu.get('institution', '')} · {edu.get('year', '')}</font>")
                edu_items.append("---")

            y = self._draw_section_classic(c, self.margin, y, left_w, "Education",
                                            edu_items)

        # Right sidebar
        sidebar_y = self.height - 58 * mm

        # Skills
        sidebar_y = self._draw_sidebar_classic(c, self.margin + left_w + 8 * mm,
                                                 sidebar_y, self.content_width - left_w - 8 * mm)

    def _draw_section_classic(self, c, x, y, width, title, content_items):
        """Draw a classic section with list of text blocks."""
        c.setFont(FONT_HEADING, 11)
        c.setFillColor(COLOR_PRIMARY)
        c.drawString(x, y, title)

        # Decorative line
        c.setStrokeColor(HexColor('#7c3aed'))
        c.setLineWidth(2)
        c.line(x, y - 2 * mm, x + 40 * mm, y - 2 * mm)

        y -= 6 * mm

        for block in content_items:
            if block == "---":
                y -= 5 * mm
                continue
            p = Paragraph(
                f'<font size="9" color="#292524">{block}</font>',
                ParagraphStyle('classic_body', fontName=FONT_BODY, fontSize=9,
                              textColor=COLOR_TEXT, leading=13, alignment=TA_JUSTIFY,
                              spaceBefore=0, spaceAfter=0)
            )
            w, h = p.wrap(width, 100 * mm)
            p.drawOn(c, x, y - h)
            y -= h + 1 * mm

        return y - 5 * mm

    def _draw_sidebar_classic(self, c, x, y, width):
        """Draw classic sidebar."""
        c.setFillColor(HexColor('#fafaf9'))
        c.rect(x, y - 80 * mm, width, 80 * mm, fill=1, stroke=0)

        c.setFont(FONT_BODY_BOLD, 8)
        c.setFillColor(HexColor('#78716c'))
        c.drawString(x + 5 * mm, y - 5 * mm, "SKILLS")
        c.setStrokeColor(HexColor('#7c3aed'))
        c.setLineWidth(1.5)
        c.line(x + 5 * mm, y - 7 * mm, x + 30 * mm, y - 7 * mm)

        # Skills
        keywords = self.profile.get('keywords', [])
        tag_x = x + 5 * mm
        tag_y = y - 14 * mm
        line_h = 7 * mm

        for kw in keywords:
            text_w = len(kw) * 2 * mm + 3 * mm
            if tag_x + text_w > x + width - 5 * mm:
                tag_x = x + 5 * mm
                tag_y -= line_h

            c.setFillColor(white)
            c.setStrokeColor(HexColor('#e7e5e4'))
            c.setLineWidth(0.3)
            c.roundRect(tag_x, tag_y - 4 * mm, text_w, 5 * mm, 1 * mm, fill=1, stroke=1)

            c.setFont(FONT_BODY, 7.5)
            c.setFillColor(COLOR_TEXT)
            c.drawString(tag_x + 1.5 * mm, tag_y - 2.5 * mm, kw[:18])

            tag_x += text_w + 2 * mm

        return y - 85 * mm

    def _render_minimal(self, c):
        """Minimal template."""
        y = self.height - 25 * mm

        # Name
        c.setFont(FONT_HEADING_BOLD, 20)
        c.setFillColor(COLOR_PRIMARY)
        c.drawString(self.margin, y, self.profile.get('title', ''))

        y -= 6 * mm

        # Contact
        c.setFont(FONT_BODY, 8)
        c.setFillColor(COLOR_TEXT_LIGHT)
        contact = ' · '.join(filter(None, [
            self.profile.get('email', ''),
            self.profile.get('location', ''),
            self.profile.get('linkedin', '')
        ]))
        c.drawString(self.margin, y, contact)

        y -= 8 * mm

        # Separator line
        c.setStrokeColor(COLOR_ACCENT)
        c.setLineWidth(2)
        c.line(self.margin, y, self.margin + 30 * mm, y)

        y -= 6 * mm

        # Profile
        p = Paragraph(
            f'<font size="9.5">{self.profile.get("profile", "")}</font>',
            ParagraphStyle('min_body', fontName=FONT_BODY, fontSize=9.5,
                          textColor=COLOR_TEXT, leading=14, alignment=TA_JUSTIFY)
        )
        w, h = p.wrap(self.content_width, 100 * mm)
        p.drawOn(c, self.margin, y - h)
        y -= h + 8 * mm

        # Experience
        for job in self.profile.get('experience', []):
            c.setFont(FONT_BODY_BOLD, 9.5)
            c.setFillColor(COLOR_PRIMARY)
            c.drawString(self.margin, y, job.get('title', ''))

            c.setFont(FONT_BODY, 8.5)
            c.setFillColor(COLOR_TEXT_LIGHT)
            period = f"{job.get('start_date', '')} — {job.get('end_date', 'Present')}"
            c.drawRightString(self.margin + self.content_width, y, period)

            y -= 4 * mm

            c.setFont(FONT_BODY, 8.5)
            c.setFillColor(HexColor('#7c3aed'))
            c.drawString(self.margin, y, job.get('company', ''))

            y -= 4 * mm

            if job.get('description'):
                p = Paragraph(
                    f'<font size="8.5" color="#374151">{job.get("description", "")}</font>',
                    ParagraphStyle('min_desc', fontName=FONT_BODY, fontSize=8.5,
                                 textColor=COLOR_TEXT, leading=12)
                )
                w, h = p.wrap(self.content_width, 100 * mm)
                p.drawOn(c, self.margin, y - h)
                y -= h + 5 * mm

        # Education
        if self.profile.get('education'):
            y -= 3 * mm
            c.setFont(FONT_BODY_BOLD, 9)
            c.setFillColor(COLOR_PRIMARY)
            c.drawString(self.margin, y, "Education")
            y -= 4 * mm
            for edu in self.profile.get('education', []):
                c.setFont(FONT_BODY_BOLD, 8.5)
                c.setFillColor(COLOR_TEXT)
                c.drawString(self.margin, y, edu.get('degree', ''))
                c.setFont(FONT_BODY, 8.5)
                c.setFillColor(COLOR_TEXT_LIGHT)
                c.drawRightString(self.margin + self.content_width, y, edu.get('year', ''))
                y -= 3 * mm
                c.setFont(FONT_BODY, 8.5)
                c.setFillColor(COLOR_TEXT_LIGHT)
                c.drawString(self.margin, y, edu.get('institution', ''))
                y -= 8 * mm

    def _render_ats_friendly(self, c):
        """ATS-friendly template - clean, maximum keyword density."""
        y = self.height - 20 * mm

        # Header block
        c.setFillColor(COLOR_PRIMARY)
        c.rect(self.margin, y - 15 * mm, self.content_width, 15 * mm, fill=1, stroke=0)

        c.setFont(FONT_HEADING_BOLD, 16)
        c.setFillColor(white)
        c.drawCentredString(self.width / 2, y - 7 * mm, self.profile.get('title', ''))

        y -= 20 * mm

        # Contact line
        contact_parts = [
            self.profile.get('email', ''),
            self.profile.get('location', ''),
            self.profile.get('linkedin', '')
        ]
        contact_str = ' | '.join(p for p in contact_parts if p)
        c.setFont(FONT_BODY, 9)
        c.setFillColor(COLOR_TEXT)
        c.drawCentredString(self.width / 2, y, contact_str)

        y -= 6 * mm

        # Divider
        c.setStrokeColor(COLOR_LINE)
        c.setLineWidth(0.5)
        c.line(self.margin, y, self.margin + self.content_width, y)

        y -= 5 * mm

        # PROFESSIONAL SUMMARY
        c.setFont(FONT_BODY_BOLD, 10)
        c.setFillColor(COLOR_PRIMARY)
        c.drawString(self.margin, y, "PROFESSIONAL SUMMARY")
        y -= 4 * mm
        c.setStrokeColor(COLOR_LINE)
        c.line(self.margin, y, self.margin + self.content_width, y)
        y -= 4 * mm

        p = Paragraph(
            f'<font size="9">{self.profile.get("profile", "")}</font>',
            ParagraphStyle('ats', fontName=FONT_BODY, fontSize=9, textColor=COLOR_TEXT,
                          leading=13, alignment=TA_JUSTIFY)
        )
        w, h = p.wrap(self.content_width, 100 * mm)
        p.drawOn(c, self.margin, y - h)
        y -= h + 5 * mm

        # CORE COMPETENCIES
        c.setFont(FONT_BODY_BOLD, 10)
        c.setFillColor(COLOR_PRIMARY)
        c.drawString(self.margin, y, "CORE COMPETENCIES")
        y -= 4 * mm
        c.setStrokeColor(COLOR_LINE)
        c.line(self.margin, y, self.margin + self.content_width, y)
        y -= 4 * mm

        # Keywords in columns
        keywords = self.profile.get('keywords', [])
        col1 = keywords[:len(keywords)//2]
        col2 = keywords[len(keywords)//2:]

        for i in range(max(len(col1), len(col2))):
            kw1 = col1[i] if i < len(col1) else ''
            kw2 = col2[i] if i < len(col2) else ''
            line = f"  • {kw1:<30}  • {kw2}" if kw2 else f"  • {kw1}"
            c.setFont(FONT_BODY, 8.5)
            c.setFillColor(COLOR_TEXT)
            c.drawString(self.margin, y, line)
            y -= 4 * mm

        y -= 3 * mm

        # PROFESSIONAL EXPERIENCE
        c.setFont(FONT_BODY_BOLD, 10)
        c.setFillColor(COLOR_PRIMARY)
        c.drawString(self.margin, y, "PROFESSIONAL EXPERIENCE")
        y -= 4 * mm
        c.setStrokeColor(COLOR_LINE)
        c.line(self.margin, y, self.margin + self.content_width, y)
        y -= 4 * mm

        for job in self.profile.get('experience', []):
            # Job header
            c.setFont(FONT_BODY_BOLD, 9.5)
            c.setFillColor(COLOR_PRIMARY)
            c.drawString(self.margin, y, job.get('title', ''))

            c.setFont(FONT_BODY, 8.5)
            c.setFillColor(COLOR_TEXT_LIGHT)
            period = f"{job.get('start_date', '')} - {job.get('end_date', 'Present')}"
            c.drawRightString(self.margin + self.content_width, y, period)
            y -= 4 * mm

            c.setFont(FONT_BODY, 9)
            c.setFillColor(HexColor('#4f46e5'))
            c.drawString(self.margin, y, job.get('company', ''))
            if job.get('location'):
                c.setFillColor(COLOR_TEXT_LIGHT)
                c.drawString(self.margin + 60 * mm, y, f" | {job.get('location', '')}")
            y -= 4 * mm

            if job.get('description'):
                p = Paragraph(
                    f'<font size="8.5">{job.get("description", "")}</font>',
                    ParagraphStyle('ats_desc', fontName=FONT_BODY, fontSize=8.5,
                                 textColor=COLOR_TEXT, leading=12)
                )
                w, h = p.wrap(self.content_width, 100 * mm)
                p.drawOn(c, self.margin, y - h)
                y -= h + 4 * mm

            y -= 3 * mm

        # EDUCATION
        if self.profile.get('education'):
            y -= 2 * mm
            c.setFont(FONT_BODY_BOLD, 10)
            c.setFillColor(COLOR_PRIMARY)
            c.drawString(self.margin, y, "EDUCATION")
            y -= 4 * mm
            c.setStrokeColor(COLOR_LINE)
            c.line(self.margin, y, self.margin + self.content_width, y)
            y -= 4 * mm

            for edu in self.profile.get('education', []):
                c.setFont(FONT_BODY_BOLD, 9)
                c.setFillColor(COLOR_TEXT)
                c.drawString(self.margin, y, edu.get('degree', ''))
                c.setFont(FONT_BODY, 9)
                c.setFillColor(COLOR_TEXT_LIGHT)
                c.drawRightString(self.margin + self.content_width, y, edu.get('year', ''))
                y -= 4 * mm
                c.setFont(FONT_BODY, 8.5)
                c.setFillColor(COLOR_TEXT_LIGHT)
                c.drawString(self.margin, y, edu.get('institution', ''))
                y -= 8 * mm


def generate_pdf(profile_path: str, output_path: str, template: str = 'modern'):
    """Generate a PDF from a JSON profile."""
    import json
    with open(profile_path, 'r', encoding='utf-8') as f:
        profile = json.load(f)

    renderer = CVRenderer(profile)
    renderer.render(output_path, template)
