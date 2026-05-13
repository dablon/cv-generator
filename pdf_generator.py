"""
Professional PDF CV Generator using ReportLab.

This module creates high-quality, ATS-friendly PDFs with premium design.
Supports multiple template styles: modern, classic, minimal, and ats-friendly.

Usage:
    from pdf_generator import CVRenderer
    renderer = CVRenderer(profile_data)
    renderer.render('output.pdf', template='modern')
"""

import os
import platform
import sys
from pathlib import Path
from typing import Optional

from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


# Configure module-level logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Default fonts (Helvetica - always available in ReportLab)
FONT_BODY = 'Helvetica'
FONT_BODY_BOLD = 'Helvetica-Bold'
FONT_HEADING = 'Helvetica'
FONT_HEADING_BOLD = 'Helvetica-Bold'


def _register_fonts() -> None:
    """Register system fonts with cross-platform support.

    Attempts to register DejaVu fonts for better typography. Falls back to
    Helvetica (default in ReportLab) if DejaVu is not available.

    Sets global font variables:
    - FONT_BODY, FONT_BODY_BOLD: For body text
    - FONT_HEADING, FONT_HEADING_BOLD: For headings

    Returns:
        None. Modifies module-level global font variables.
    """
    global FONT_BODY, FONT_BODY_BOLD, FONT_HEADING, FONT_HEADING_BOLD

    system = platform.system()
    font_dir = None

    # Determine font directory based on OS
    if system == 'Linux':
        font_dir = "/usr/share/fonts/truetype/dejavu/"
    elif system == 'Windows':
        font_dir = "C:\\Windows\\Fonts\\"
    elif system == 'Darwin':  # macOS
        font_dir = "/Library/Fonts/"

    # Try to register DejaVu fonts if directory exists
    if font_dir and Path(font_dir).exists():
        try:
            # Check if DejaVu fonts actually exist
            dejavu_sans = Path(font_dir + 'DejaVuSans.ttf')
            if dejavu_sans.exists():
                pdfmetrics.registerFont(TTFont('DejaVuSans', font_dir + 'DejaVuSans.ttf'))
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', font_dir + 'DejaVuSans-Bold.ttf'))
                pdfmetrics.registerFont(TTFont('DejaVuSerif', font_dir + 'DejaVuSerif.ttf'))
                pdfmetrics.registerFont(TTFont('DejaVuSerif-Bold', font_dir + 'DejaVuSerif-Bold.ttf'))

                FONT_BODY = 'DejaVuSans'
                FONT_BODY_BOLD = 'DejaVuSans-Bold'
                FONT_HEADING = 'DejaVuSerif'
                FONT_HEADING_BOLD = 'DejaVuSerif-Bold'

                logger.debug("DejaVu fonts registered successfully")
                return
        except Exception as e:
            logger.debug(f"Could not register DejaVu fonts: {e}")
            # Fall through to Helvetica

    logger.debug("Using default Helvetica fonts")


# Initialize fonts on module load
_register_fonts()


# Color palette
COLOR_PRIMARY = HexColor('#1a1a2e')       # Dark navy - main headings
COLOR_ACCENT = HexColor('#4f46e5')        # Indigo - accent elements
COLOR_ACCENT_LIGHT = HexColor('#818cf8')   # Light indigo - secondary accents
COLOR_TEXT = HexColor('#1e293b')           # Dark slate - body text
COLOR_TEXT_LIGHT = HexColor('#64748b')    # Gray - secondary text
COLOR_BG = HexColor('#f8fafc')             # Off-white - backgrounds
COLOR_LINE = HexColor('#e2e8f0')           # Light gray - dividers
COLOR_SIDEBAR = HexColor('#f1f5f9')        # Very light gray - sidebar bg


class CVRenderer:
    """Renders a CV profile into a professional PDF document.

    This class takes a CV profile dictionary and generates a formatted PDF
    using the ReportLab library. Supports multiple template styles with
    consistent formatting and professional design.

    Attributes:
        profile: Dictionary containing CV data with keys like:
                 title, profile, keywords, experience, education, email, location, linkedin.
        width: Page width in points (A4).
        height: Page height in points (A4).
        margin: Page margin in millimeters.
        content_width: Usable content width (page width - 2 * margin).

    Example:
        profile = {
            'title': 'Senior Software Engineer',
            'profile': 'Experienced developer...',
            'keywords': ['Python', 'AWS', 'Docker'],
            'experience': [{'title': 'Tech Lead', 'company': 'Acme', ...}],
            'email': 'john@example.com',
            'location': 'San Francisco, CA',
            'linkedin': 'linkedin.com/in/johndoe'
        }
        renderer = CVRenderer(profile)
        renderer.render('output.pdf', 'modern')
    """

    def __init__(self, profile: dict) -> None:
        """Initialize the CV renderer with profile data.

        Args:
            profile: Dictionary containing CV data. Expected keys include:
                     - title (str): Job title or name
                     - profile (str): Professional summary
                     - keywords (list): List of skill strings
                     - experience (list): List of job dictionaries
                     - education (list): List of education dictionaries
                     - email (str): Email address
                     - location (str): Location string
                     - linkedin (str): LinkedIn URL or username
                     - languages (list): List of language dictionaries
                     - certifications (list): List of certification strings
        """
        self.profile = profile
        self.width, self.height = A4
        self.margin = 25 * mm
        self.bottom_margin = 20 * mm
        self.content_width = self.width - 2 * self.margin
        self.page_min_y = self.bottom_margin
        self.header_height = 50 * mm
        self.sidebar_width = self.content_width * 0.32

    def render(self, output_path: str, template: str = 'modern') -> None:
        """Render the CV to a PDF file.

        Main entry point for generating the PDF. Dispatches to the appropriate
        template renderer based on the template name.

        Args:
            output_path: Path where the PDF will be saved.
            template: Template style to use. Options:
                      - 'modern': Two-column layout with sidebar
                      - 'classic': Traditional elegant design
                      - 'minimal': Clean, minimalist layout
                      - 'ats-friendly': Optimized for ATS systems

        Raises:
            IOError: If the PDF cannot be written to the output path.
            ValueError: If an invalid template is specified.

        Example:
            renderer = CVRenderer(profile)
            renderer.render('cv.pdf', template='modern')
        """
        logger.info(f"Rendering PDF with template: {template}")
        logger.debug(f"Output path: {output_path}")

        c = canvas.Canvas(output_path, pagesize=A4)
        c.setTitle(self.profile.get('title', 'CV'))
        c.setAuthor(self.profile.get('email', ''))

        # Dispatch to appropriate template renderer
        template_renderers = {
            'modern': self._render_modern,
            'classic': self._render_classic,
            'minimal': self._render_minimal,
            'ats-friendly': self._render_ats_friendly,
        }

        renderer = template_renderers.get(template, self._render_modern)
        renderer(c)

        c.save()
        logger.info(f"PDF saved successfully: {output_path}")

    def _new_page(self, c: canvas.Canvas) -> float:
        """Start a new page, returning the top Y position."""
        c.showPage()
        return self.height - self.margin

    def _draw_header_modern(self, c: canvas.Canvas) -> None:
        """Draw the header section for the modern template.

        Creates a visually rich header with:
        - Colored background (dark navy)
        - Accent bar
        - Decorative gradient effect
        - Name and role
        - Contact information card

        Args:
            c: ReportLab canvas object for drawing.

        Note:
            This is an internal method called by _render_modern.
        """
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

        # Name - use profile 'name' or fallback to title
        name = self.profile.get('name', self.profile.get('title', ''))
        c.setFillColor(white)
        c.setFont(FONT_HEADING_BOLD, 22)
        c.drawString(self.margin, self.height - 28 * mm, name)

        # Subtitle (role/title)
        c.setFont(FONT_BODY, 9)
        c.setFillColor(HexColor('#a5b4fc'))
        role = self.profile.get('title', '')  # title is actually the role
        c.drawString(self.margin, self.height - 35 * mm, role)

        # Contact card (right side)
        card_x = self.width - self.margin - 55 * mm
        card_y = self.height - 22 * mm
        card_w = 55 * mm
        card_h = 35 * mm

        c.setFillColor(HexColor('#ffffff15'))
        c.roundRect(card_x, card_y - card_h + 5 * mm, card_w, card_h, 3 * mm, fill=1, stroke=0)

        # Contact info (without emojis for PDF compatibility)
        c.setFont(FONT_BODY, 7.5)
        c.setFillColor(white)
        contact_y = self.height - 26 * mm
        # Email
        c.setFillColor(HexColor('#a5b4fc'))
        c.drawString(card_x + 4 * mm, contact_y, "Email:")
        c.setFillColor(white)
        email = self.profile.get('email', '') or ''
        c.drawString(card_x + 22 * mm, contact_y, email[:28] if email else '')
        # Location
        c.setFillColor(HexColor('#a5b4fc'))
        c.drawString(card_x + 4 * mm, contact_y - 7 * mm, "Loc:")
        c.setFillColor(white)
        location = self.profile.get('location', '') or ''
        c.drawString(card_x + 22 * mm, contact_y - 7 * mm, location[:28] if location else '')
        # LinkedIn
        c.setFillColor(HexColor('#a5b4fc'))
        c.drawString(card_x + 4 * mm, contact_y - 14 * mm, "LinkedIn:")
        c.setFillColor(white)
        linkedin = self.profile.get('linkedin', '') or ''
        if linkedin.startswith('http'):
            linkedin = linkedin.split('/')[-1] if '/' in linkedin else linkedin
        c.drawString(card_x + 22 * mm, contact_y - 14 * mm, linkedin[:28] if linkedin else '')

    def _render_modern(self, c: canvas.Canvas) -> None:
        """Render the modern template with two-column layout.

        Creates a modern CV design with:
        - Left column (60%): Profile, Experience, Education, Certifications
        - Right column (37%): Skills sidebar, Languages

        Args:
            c: ReportLab canvas object for drawing.

        Note:
            This is an internal method called by render().
        """
        self._draw_header_modern(c)

        y = self.height - 62 * mm
        # Fixed column widths - left takes 60%, right takes 37%, gap 3%
        left_col_w = self.content_width * 0.60
        right_col_w = self.content_width * 0.37
        col_gap = self.content_width * 0.03

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
        # Match the starting Y position of the left column content
        sidebar_y = self.height - 62 * mm

        # Skills (always show)
        sidebar_y = self._draw_sidebar_skills(c, right_x, sidebar_y, right_col_w)

        # Languages
        if self.profile.get('languages'):
            sidebar_y = self._draw_sidebar_languages(c, right_x, sidebar_y, right_col_w)

    def _draw_section_modern(
        self,
        c: canvas.Canvas,
        x: float,
        y: float,
        width: float,
        num: str,
        title: str,
        content_items: list
    ) -> float:
        """Draw a numbered section with title and content for modern template.

        Args:
            c: ReportLab canvas object.
            x: Starting X position.
            y: Starting Y position.
            width: Section width.
            num: Section number (e.g., "01", "02").
            title: Section title.
            content_items: List of content elements (Paragraphs or other drawables).

        Returns:
            New Y position after the section content.

        Note:
            This is an internal method called by _render_modern.
        """
        # Section header (8mm height + 2mm underline)
        section_h = 10 * mm
        if y - section_h < self.page_min_y:
            y = self._new_page(c)

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
                if y - h < self.page_min_y:
                    y = self._new_page(c)
                item.drawOn(c, x, y - h)
                y -= h + 3 * mm
            elif hasattr(item, 'drawOn'):
                if y - 15 * mm < self.page_min_y:
                    y = self._new_page(c)
                item.drawOn(c, x, y)
                y -= 15 * mm

        return y

    def _render_experience_modern(self, c: canvas.Canvas, x: float, y: float, width: float) -> list:
        """Render experience items for modern template.

        Creates formatted paragraphs for each job entry including:
        - Period (dates)
        - Title (job title)
        - Company (with optional location)
        - Description

        Args:
            c: ReportLab canvas object (unused, kept for API consistency).
            x: Starting X position (unused).
            y: Starting Y position (unused).
            width: Content width (unused).

        Returns:
            List of Paragraph objects for experience entries.

        Note:
            This is an internal method called by _render_modern.
        """
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

    def _render_education_modern(self, c: canvas.Canvas, x: float, y: float, width: float) -> list:
        """Render education items for modern template.

        Creates formatted paragraphs for each education entry including:
        - Year
        - Degree
        - Institution

        Args:
            c: ReportLab canvas object (unused).
            x: Starting X position (unused).
            y: Starting Y position (unused).
            width: Content width (unused).

        Returns:
            List of Paragraph objects for education entries.

        Note:
            This is an internal method called by _render_modern.
        """
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

    def _render_certifications_modern(self, c: canvas.Canvas, x: float, y: float, width: float) -> list:
        """Render certification badges for modern template.

        Creates a formatted paragraph with all certifications separated by bullets.

        Args:
            c: ReportLab canvas object (unused).
            x: Starting X position (unused).
            y: Starting Y position (unused).
            width: Content width (unused).

        Returns:
            List containing one Paragraph with all certifications.

        Note:
            This is an internal method called by _render_modern.
        """
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

    def _draw_sidebar_skills(self, c: canvas.Canvas, x: float, y: float, width: float) -> float:
        """Draw skills sidebar section for modern template.

        Creates a card with skill tags displayed in a wrapped layout.

        Args:
            c: ReportLab canvas object.
            x: Starting X position.
            y: Starting Y position.
            width: Sidebar width.

        Returns:
            New Y position after the skills section.

        Note:
            This is an internal method called by _render_modern.
        """
        # Background card
        card_h = 60 * mm
        if y - card_h < self.page_min_y:
            y = self._new_page(c)

        c.setFillColor(COLOR_BG)
        c.roundRect(x, y - card_h, width, card_h, 3 * mm, fill=1, stroke=0)
        c.setStrokeColor(COLOR_LINE)
        c.setLineWidth(0.5)
        c.roundRect(x, y - card_h, width, card_h, 3 * mm, fill=0, stroke=1)

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
                if tag_y - 8 * mm < self.page_min_y:
                    y = self._new_page(c)
                    tag_y = y - 12 * mm

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

    def _draw_sidebar_languages(self, c: canvas.Canvas, x: float, y: float, width: float) -> float:
        """Draw languages sidebar section for modern template.

        Creates language cards showing language name and proficiency level.

        Args:
            c: ReportLab canvas object.
            x: Starting X position.
            y: Starting Y position.
            width: Sidebar width.

        Returns:
            New Y position after the languages section.

        Note:
            This is an internal method called by _render_modern.
        """
        card_h = 20 * mm
        if y - card_h < self.page_min_y:
            y = self._new_page(c)

        # Title
        c.setFont(FONT_BODY_BOLD, 8)
        c.setFillColor(COLOR_TEXT_LIGHT)
        c.drawString(x + 4 * mm, y - 6 * mm, "LANGUAGES")

        y -= 12 * mm

        for lang in self.profile.get('languages', []):
            if y - 11 * mm < self.page_min_y:
                y = self._new_page(c)
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

    def _body_style(self) -> ParagraphStyle:
        """Create the body text paragraph style.

        Returns:
            ParagraphStyle configured for body text with justified alignment.
        """
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

    def _render_classic(self, c: canvas.Canvas) -> None:
        """Render the classic elegant template.

        Creates a traditional CV design with:
        - Dark header with accent line
        - Name and contact information
        - Two-column layout with sidebar

        Args:
            c: ReportLab canvas object for drawing.

        Note:
            This is an internal method called by render().
        """
        # Header
        c.setFillColor(COLOR_PRIMARY)
        c.rect(0, self.height - self.header_height, self.width, self.header_height, fill=1, stroke=0)

        # Accent line
        c.setFillColor(HexColor('#7c3aed'))
        c.rect(self.margin, self.height - self.header_height - 1.5 * mm, 80 * mm, 1.5 * mm, fill=1, stroke=0)

        # Name
        c.setFont(FONT_HEADING_BOLD, 22)
        c.setFillColor(white)
        c.drawString(self.margin, self.height - 28 * mm, self.profile.get('title', ''))

        # Subtitle (below name)
        c.setFont(FONT_BODY, 9)
        c.setFillColor(HexColor('#a78bfa'))
        c.drawString(self.margin, self.height - 36 * mm, self.profile.get('subtitle', ''))

        # Contact (right side)
        c.setFont(FONT_BODY, 8)
        c.setFillColor(HexColor('#ffffffcc'))
        contact_items = [
            self.profile.get('email', ''),
            self.profile.get('location', ''),
            self.profile.get('linkedin', '')
        ]
        contact_str = ' · '.join(c for c in contact_items if c)
        c.drawRightString(self.width - self.margin, self.height - 28 * mm, contact_str)

        # Content area - below header
        y = self.height - self.header_height - 8 * mm
        # Left column: 65% of content width
        left_w = self.content_width * 0.63
        # Right column: skills sidebar
        sidebar_x = self.margin + left_w + 5 * mm
        sidebar_w = self.content_width - left_w - 5 * mm
        sidebar_y = y

        # Profile section
        y = self._draw_section_classic(c, self.margin, y, left_w, "Profile",
                                        [self.profile.get('profile', '')])

        y -= 3 * mm

        # Experience section
        if self.profile.get('experience'):
            items = []
            for job in self.profile.get('experience', []):
                period = f"{job.get('start_date', '')} - {job.get('end_date', 'Present')}"
                items.append(f"<b>{job.get('title', '')}</b>")
                items.append(f"<font color='#7c3aed'>{job.get('company', '')}{' · ' + job['location'] if job.get('location') else ''}</font>")
                items.append(f"<font color='#78716c' size='7.5'>{period}</font>")
                desc = job.get('description', '')
                if desc:
                    items.append(f"<font size='8'>{desc}</font>")
                items.append("---")

            y = self._draw_section_classic(c, self.margin, y, left_w, "Experience", items)

        # Education section
        if self.profile.get('education'):
            edu_items = []
            for edu in self.profile.get('education', []):
                edu_items.append(f"<b>{edu.get('degree', '')}</b>")
                edu_items.append(f"<font color='#78716c'>{edu.get('institution', '')} · {edu.get('year', '')}</font>")
                edu_items.append("---")

            y = self._draw_section_classic(c, self.margin, y, left_w, "Education", edu_items)

        # Right sidebar - Skills (drawn independently of left content position)
        self._draw_sidebar_classic(c, sidebar_x, sidebar_y, sidebar_w)

    def _draw_section_classic(
        self,
        c: canvas.Canvas,
        x: float,
        y: float,
        width: float,
        title: str,
        content_items: list
    ) -> float:
        """Draw a section for the classic template with list of text blocks.

        Args:
            c: ReportLab canvas object.
            x: Starting X position.
            y: Starting Y position.
            width: Section width.
            title: Section title.
            content_items: List of content strings or "---" separators.

        Returns:
            New Y position after the section content.

        Note:
            This is an internal method called by _render_classic.
        """
        section_h = 8 * mm
        if y - section_h < self.page_min_y:
            y = self._new_page(c)

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
            if y - h < self.page_min_y:
                y = self._new_page(c)
            p.drawOn(c, x, y - h)
            y -= h + 1 * mm

        return y - 5 * mm

    def _draw_sidebar_classic(self, c: canvas.Canvas, x: float, y: float, width: float) -> float:
        """Draw classic sidebar with skills.

        Args:
            c: ReportLab canvas object.
            x: Starting X position.
            y: Starting Y position (top of sidebar area).
            width: Sidebar width.

        Returns:
            New Y position after the sidebar.

        Note:
            This is an internal method called by _render_classic.
        """
        # Title
        c.setFont(FONT_BODY_BOLD, 8)
        c.setFillColor(HexColor('#78716c'))
        c.drawString(x, y, "SKILLS")
        c.setStrokeColor(HexColor('#7c3aed'))
        c.setLineWidth(1.5)
        c.line(x, y - 2 * mm, x + 30 * mm, y - 2 * mm)

        y -= 8 * mm

        # Skills - draw as wrapped tags
        keywords = self.profile.get('keywords', [])
        tag_x = x
        tag_y = y
        tag_h = 5 * mm
        line_h = 6.5 * mm
        max_x = x + width

        for kw in keywords:
            text_w = len(kw) * 1.8 * mm + 3 * mm
            # Wrap to next line if needed
            if tag_x + text_w > max_x:
                tag_x = x
                tag_y -= line_h

            c.setFillColor(white)
            c.setStrokeColor(HexColor('#e7e5e4'))
            c.setLineWidth(0.3)
            c.roundRect(tag_x, tag_y - tag_h, text_w, tag_h, 1 * mm, fill=1, stroke=1)

            c.setFont(FONT_BODY, 7)
            c.setFillColor(COLOR_TEXT)
            c.drawString(tag_x + 1.5 * mm, tag_y - 3 * mm, kw[:20])

            tag_x += text_w + 2 * mm

        return tag_y - line_h

    def _render_minimal(self, c: canvas.Canvas) -> None:
        """Render the minimal template.

        Creates a clean, minimalist CV design with:
        - Simple name and contact header
        - Clean section separators
        - Single-column layout

        Args:
            c: ReportLab canvas object for drawing.

        Note:
            This is an internal method called by render().
        """
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
        if y - h < self.page_min_y:
            y = self._new_page(c)
        p.drawOn(c, self.margin, y - h)
        y -= h + 8 * mm

        # Experience
        for job in self.profile.get('experience', []):
            if y - 20 * mm < self.page_min_y:
                y = self._new_page(c)

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
                if y - h < self.page_min_y:
                    y = self._new_page(c)
                p.drawOn(c, self.margin, y - h)
                y -= h + 5 * mm

        # Education
        if self.profile.get('education'):
            if y - 30 * mm < self.page_min_y:
                y = self._new_page(c)
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

    def _render_ats_friendly(self, c: canvas.Canvas) -> None:
        """Render the ATS-friendly template.

        Creates a clean, optimized layout for Applicant Tracking Systems:
        - Maximum keyword density
        - Clean section headers
        - Simple formatting without complex layouts

        Args:
            c: ReportLab canvas object for drawing.

        Note:
            This is an internal method called by render().
        """
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
        if y - h < self.page_min_y:
            y = self._new_page(c)
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
            if y - 4 * mm < self.page_min_y:
                y = self._new_page(c)
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
            if y - 20 * mm < self.page_min_y:
                y = self._new_page(c)
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
                if y - h < self.page_min_y:
                    y = self._new_page(c)
                p.drawOn(c, self.margin, y - h)
                y -= h + 4 * mm

            y -= 3 * mm

        # EDUCATION
        if self.profile.get('education'):
            if y - 30 * mm < self.page_min_y:
                y = self._new_page(c)
            y -= 2 * mm
            c.setFont(FONT_BODY_BOLD, 10)
            c.setFillColor(COLOR_PRIMARY)
            c.drawString(self.margin, y, "EDUCATION")
            y -= 4 * mm
            c.setStrokeColor(COLOR_LINE)
            c.line(self.margin, y, self.margin + self.content_width, y)
            y -= 4 * mm

            for edu in self.profile.get('education', []):
                if y - 10 * mm < self.page_min_y:
                    y = self._new_page(c)
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


def generate_pdf(profile_path: str, output_path: str, template: str = 'modern') -> None:
    """Generate a PDF from a JSON profile file.

    This is a convenience function that loads a JSON profile and renders it
    as a PDF using the CVRenderer class.

    Args:
        profile_path: Path to the JSON profile file.
        output_path: Path where the PDF will be saved.
        template: Template style to use. Options:
                  'modern', 'classic', 'minimal', 'ats-friendly'.
                  Defaults to 'modern'.

    Raises:
        FileNotFoundError: If the profile file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        IOError: If the PDF cannot be written.

    Example:
        generate_pdf('profile.json', 'cv.pdf', template='classic')
    """
    import json

    logger.info(f"Generating PDF from: {profile_path}")

    with open(profile_path, 'r', encoding='utf-8') as f:
        profile = json.load(f)

    renderer = CVRenderer(profile)
    renderer.render(output_path, template)

    logger.info(f"PDF generated: {output_path}")