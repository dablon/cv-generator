"""
Professional PDF CV Generator — Canvas-based for full layout control.
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from pathlib import Path
import json


# ─── Fonts ───────────────────────────────────────────────────────────────────
FONT_DIR = "/usr/share/fonts/truetype/dejavu/"

def _load_fonts():
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont('D',      FONT_DIR + 'DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DB',     FONT_DIR + 'DejaVuSans-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('DSerif', FONT_DIR + 'DejaVuSerif.ttf'))
        pdfmetrics.registerFont(TTFont('DSB',    FONT_DIR + 'DejaVuSerif-Bold.ttf'))
        return 'D', 'DB', 'DSerif', 'DSB'
    except:
        return 'Helvetica', 'Helvetica-Bold', 'Helvetica', 'Helvetica-Bold'

FD, FDB, FS, FSB = _load_fonts()

# ─── Colors ──────────────────────────────────────────────────────────────────
C_NAVY   = HexColor('#0f172a')
C_PURPLE = HexColor('#4f46e5')
C_LAVEND = HexColor('#a78bfa')
C_PALE   = HexColor('#eef2ff')
C_PINK   = HexColor('#ec4899')
C_TEAL   = HexColor('#0d9488')
C_GOLD   = HexColor('#d4af37')
C_WHITE  = HexColor('#ffffff')
C_TEXT   = HexColor('#1f2937')
C_MID    = HexColor('#6b7280')
C_BG     = HexColor('#f8fafc')
C_BG2    = HexColor('#fafaf9')
C_LINE   = HexColor('#e5e7eb')