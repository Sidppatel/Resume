"""
Styles and OpenXML helpers for Executive & ATS Gold-Standard Resume Formatting.
Conforms to Harvard/Wharton & FAANG single-column ATS resume specifications.
"""
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn


class ResumeStyles:
    """
    Standardized typography, dimensions, spacing, and styling tokens.
    """
    FONT_FAMILY = "Times New Roman"
    COLOR_BLACK = RGBColor(0x00, 0x00, 0x00)
    COLOR_MUTED = RGBColor(0x33, 0x33, 0x33)

    # Page setup: Standard US Letter with 0.5 in (36pt) margins
    PAGE_WIDTH = Inches(8.5)
    PAGE_HEIGHT = Inches(11.0)
    MARGIN_TOP = Inches(0.5)
    MARGIN_BOTTOM = Inches(0.5)
    MARGIN_LEFT = Inches(0.5)
    MARGIN_RIGHT = Inches(0.5)
    CONTENT_WIDTH = Inches(7.5)  # 8.5" - 2*(0.5") = 7.5" text body width

    # Standard typographic hierarchy (Points)
    NAME_SIZE = Pt(16.5)
    TITLE_SIZE = Pt(12.0)
    SECTION_HEADING_SIZE = Pt(11.0)
    ENTRY_TITLE_SIZE = Pt(10.5)
    BODY_SIZE = Pt(10.0)
    CONTACT_SIZE = Pt(9.5)

    # Bullet indentation standards
    BULLET_LEFT_INDENT = Inches(0.22)
    BULLET_FIRST_LINE_INDENT = Inches(-0.22)

    # Line and paragraph spacing (Points / multipliers)
    LINE_SPACING = 1.08
    TITLE_BEFORE = Pt(6.0)
    TITLE_AFTER = Pt(7.0)
    SECTION_BEFORE = Pt(7.0)
    SECTION_AFTER = Pt(2.5)
    ENTRY_BEFORE = Pt(4.0)
    ENTRY_AFTER = Pt(1.0)
    BULLET_BEFORE = Pt(0.5)
    BULLET_AFTER = Pt(1.5)


def apply_page_setup(doc):
    """Applies standardized page dimensions and margins across all sections."""
    for section in doc.sections:
        section.page_width = ResumeStyles.PAGE_WIDTH
        section.page_height = ResumeStyles.PAGE_HEIGHT
        section.top_margin = ResumeStyles.MARGIN_TOP
        section.bottom_margin = ResumeStyles.MARGIN_BOTTOM
        section.left_margin = ResumeStyles.MARGIN_LEFT
        section.right_margin = ResumeStyles.MARGIN_RIGHT


def add_section_bottom_line(paragraph, sz="6", color="000000"):
    """
    Adds a crisp horizontal bottom border line beneath a section heading.
    sz="6" corresponds to a clean 0.75pt rule spanning the full content width.
    """
    pPr = paragraph._p.get_or_add_pPr()
    pBdr_xml = f"""
    <w:pBdr {nsdecls('w')}>
      <w:bottom w:val="single" w:sz="{sz}" w:space="1" w:color="{color}"/>
    </w:pBdr>
    """
    pPr.append(parse_xml(pBdr_xml))


def add_horizontal_borders(paragraph, sz="10", space="4", color="000000"):
    """
    Adds top and bottom horizontal border lines with clean internal padding to frame the target title.
    """
    pPr = paragraph._p.get_or_add_pPr()
    pBdr_xml = f"""
    <w:pBdr {nsdecls('w')}>
      <w:top w:val="single" w:sz="{sz}" w:space="{space}" w:color="{color}"/>
      <w:bottom w:val="single" w:sz="{sz}" w:space="{space}" w:color="{color}"/>
    </w:pBdr>
    """
    pPr.append(parse_xml(pBdr_xml))


def configure_right_tab_stop(paragraph, position=Inches(7.5)):
    """Add a right-aligned tab stop for perfect two-column date/location alignment."""
    paragraph.paragraph_format.tab_stops.add_tab_stop(position, WD_TAB_ALIGNMENT.RIGHT)


def set_run_font(run, font_name=ResumeStyles.FONT_FAMILY, size=ResumeStyles.BODY_SIZE, bold=False, italic=False, underline=False, color=None):
    """
    Applies typographic formatting with explicit OpenXML fonts for consistent cross-platform Word/PDF rendering.
    """
    run.font.name = font_name
    run.font.size = size
    run.bold = bold
    run.italic = italic
    run.underline = underline
    run.font.color.rgb = color if color else ResumeStyles.COLOR_BLACK

    # Explicitly set OpenXML font family attributes (ascii, hAnsi, cs, eastAsia)
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is not None:
        rFonts.set(qn('w:ascii'), font_name)
        rFonts.set(qn('w:hAnsi'), font_name)
        rFonts.set(qn('w:cs'), font_name)
        rFonts.set(qn('w:eastAsia'), font_name)
