"""
Generador de la presentación corporativa de PortIO.

PortIO - Inteligencia operativa marítima y portuaria en tiempo real.

Estructura de la presentación:
  - Resumen ejecutivo            → qué es PortIO de un vistazo.
  - Bloque 1 · Visión general    → propósito, necesidad → capacidad, los 3 módulos.
  - Bloque 2 · Recorrido         → tour por las 10 pantallas (con capturas reales).
  - Bloque 3 · Valor para el puerto → Smart Port, asistente de IA, tiempo real.

Diseño alineado con la plataforma web (azul de marca #003A8C + acento cian del
logo radar + ámbar de estados). Las capturas viven en ../screenshots y se
regeneran con `npm run screenshot` desde portIO-frontend.

Salida: «Presentación PortIO.pdf» en este mismo directorio.

Uso:
    cd portIO-docs/presentacion
    python3 build_pdf.py
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, Image, KeepTogether, NextPageTemplate,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.graphics.shapes import Circle, Drawing, Line, Rect, String

# -----------------------------------------------------------------------------
# Paths & constants
# -----------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent           # portIO-docs/presentacion
DOCS = HERE.parent                               # portIO-docs
SCREENSHOTS = DOCS / "screenshots"
OUTPUT_PDF = HERE / "Presentación PortIO.pdf"
# Logo oficial de la plataforma: wordmark "portIO" con el isotipo radar como
# «O», capturado del sidebar de la app (a[aria-label="portIO"]) sobre fondo
# transparente a 4x. Si la marca cambia, recapturar ese elemento aquí.
LOGO = HERE / "assets" / "logo-wordmark.png"
# Silueta blanca del wordmark, para cabeceras sobre el panel navy (divisores).
LOGO_WHITE = HERE / "assets" / "logo-wordmark-white.png"


def _logo_ratio() -> float:
    """Relación ancho/alto real del PNG del logo, para no deformarlo."""
    try:
        from PIL import Image as _PILImage
        with _PILImage.open(LOGO) as im:
            return im.size[0] / im.size[1]
    except Exception:
        return 2.979  # fallback al ratio del wordmark capturado


LOGO_RATIO = _logo_ratio()

# Paleta de marca - alineada con tailwind.config (brand) y el logo radar.
NAVY = HexColor("#003A8C")        # brand-600, azul de marca
NAVY_DARK = HexColor("#00204F")   # brand-900
NAVY_LIGHT = HexColor("#1B559F")  # brand-500
NAVY_FAINT = HexColor("#9DB4D6")  # anillo exterior del radar (navy translúcido)
CYAN = HexColor("#EAB308")        # acento de marca en amarillo (antes cyan #06B6D4)
CYAN_LIGHT = HexColor("#CFFAFE")  # cyan-100
AMBER = HexColor("#EAB308")       # ámbar de estados/alertas
AMBER_LIGHT = HexColor("#FDE68A")
TEAL = HexColor("#0E7C7B")
SLATE = HexColor("#475569")
SLATE_LIGHT = HexColor("#94A3B8")
SLATE_BG = HexColor("#F1F5F9")
WHITE = colors.white
BLACK = HexColor("#0F172A")       # slate-900, color de "port" en el wordmark
EMERALD = HexColor("#10B981")

PAGE_W, PAGE_H = A4
MARGIN_L = 26 * mm
MARGIN_R = 26 * mm
MARGIN_T = 28 * mm
MARGIN_B = 26 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R


# -----------------------------------------------------------------------------
# Styles
# -----------------------------------------------------------------------------

styles = getSampleStyleSheet()

ST_KICKER = ParagraphStyle("Kicker", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=9, leading=11,
    textColor=CYAN, alignment=TA_LEFT, spaceAfter=4)
ST_H1 = ParagraphStyle("H1", parent=styles["Heading1"],
    fontName="Helvetica-Bold", fontSize=22, leading=28,
    textColor=NAVY, alignment=TA_LEFT, spaceBefore=14, spaceAfter=12)
ST_H2 = ParagraphStyle("H2", parent=styles["Heading2"],
    fontName="Helvetica-Bold", fontSize=15, leading=20,
    textColor=NAVY, alignment=TA_LEFT, spaceBefore=18, spaceAfter=8)
ST_H3 = ParagraphStyle("H3", parent=styles["Heading3"],
    fontName="Helvetica-Bold", fontSize=12, leading=16,
    textColor=NAVY, alignment=TA_LEFT, spaceBefore=12, spaceAfter=6)
ST_BLOCK_LABEL = ParagraphStyle("BlockLabel", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=10, leading=12,
    textColor=CYAN, alignment=TA_LEFT, spaceAfter=2)
ST_BLOCK_TITLE = ParagraphStyle("BlockTitle", parent=styles["Title"],
    fontName="Helvetica-Bold", fontSize=28, leading=34,
    textColor=NAVY, alignment=TA_LEFT, spaceAfter=8)
ST_BODY = ParagraphStyle("Body", parent=styles["BodyText"],
    fontName="Helvetica", fontSize=10, leading=15,
    textColor=BLACK, alignment=TA_JUSTIFY, spaceAfter=8)
ST_BODY_LEAD = ParagraphStyle("BodyLead", parent=ST_BODY,
    fontSize=11, leading=17, textColor=SLATE, spaceAfter=12)
ST_LI = ParagraphStyle("ListItem", parent=ST_BODY,
    leftIndent=16, bulletIndent=4, spaceAfter=4)
ST_CAPTION = ParagraphStyle("Caption", parent=styles["Normal"],
    fontName="Helvetica-Oblique", fontSize=8.5, leading=12,
    textColor=SLATE, alignment=TA_LEFT, spaceBefore=4, spaceAfter=14)
ST_NOTE = ParagraphStyle("Note", parent=styles["Normal"],
    fontName="Helvetica", fontSize=9, leading=13,
    textColor=SLATE, alignment=TA_LEFT,
    leftIndent=10, rightIndent=10, spaceAfter=8,
    backColor=SLATE_BG, borderPadding=8)
ST_QUOTE = ParagraphStyle("Quote", parent=styles["Normal"],
    fontName="Helvetica-Oblique", fontSize=12.5, leading=18,
    textColor=NAVY_LIGHT, alignment=TA_LEFT,
    leftIndent=14, rightIndent=14, spaceBefore=8, spaceAfter=10,
    borderColor=CYAN, borderPadding=10)
ST_TABLE_HEAD = ParagraphStyle("TableHead", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=9, leading=11,
    textColor=WHITE, alignment=TA_LEFT)
ST_TABLE_CELL = ParagraphStyle("TableCell", parent=styles["Normal"],
    fontName="Helvetica", fontSize=9, leading=12,
    textColor=BLACK, alignment=TA_LEFT)
ST_TABLE_CELL_BOLD = ParagraphStyle("TableCellBold", parent=ST_TABLE_CELL,
    fontName="Helvetica-Bold", textColor=NAVY)
ST_KPI_NUM = ParagraphStyle("KpiNum", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=17, leading=21,
    textColor=WHITE, alignment=TA_CENTER, spaceAfter=0)
ST_KPI_LABEL = ParagraphStyle("KpiLabel", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=8.5, leading=11,
    textColor=NAVY, alignment=TA_CENTER)


# -----------------------------------------------------------------------------
# Marca - logo radar de PortIO
# -----------------------------------------------------------------------------

def logo_image(width: float) -> Image:
    """Logo oficial de la plataforma escalado a un ancho dado, centrado."""
    img = Image(str(LOGO), width=width, height=width / LOGO_RATIO)
    img.hAlign = "CENTER"
    return img


# -----------------------------------------------------------------------------
# Page templates
# -----------------------------------------------------------------------------

def cover_background(c, doc):
    """Portada corporativa: fondo blanco, línea fina azul y banda de metadatos."""
    c.saveState()
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setStrokeColor(NAVY); c.setLineWidth(1)
    c.line(28 * mm, 38 * mm, PAGE_W - 28 * mm, 38 * mm)
    c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 9)
    c.drawString(28 * mm, 28 * mm, "PRESENTACIÓN DE PLATAFORMA")
    c.setFillColor(SLATE); c.setFont("Helvetica", 9)
    c.drawString(28 * mm, 19 * mm, "Mayo 2026  ·  Versión 1.0")
    c.setFillColor(CYAN); c.setFont("Helvetica-Bold", 9)
    c.drawRightString(PAGE_W - 28 * mm, 19 * mm, "demo.portio.es")
    c.restoreState()


def divider_background(c, doc):
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W * 0.42, PAGE_H, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(PAGE_W * 0.42 - 4, PAGE_H * 0.40, 8, PAGE_H * 0.20, fill=1, stroke=0)
    # Cabecera: wordmark blanco arriba-izquierda, sobre el panel navy.
    logo_h = 4.6 * mm
    logo_w = logo_h * LOGO_RATIO
    try:
        c.drawImage(str(LOGO_WHITE), MARGIN_L, PAGE_H - 15 * mm - 1.2 * mm,
                    width=logo_w, height=logo_h, mask="auto",
                    preserveAspectRatio=True)
    except Exception:
        pass
    c.restoreState()


def content_background(c, doc):
    """Header con wordmark portIO + tagline; footer con paginación."""
    c.saveState()
    # HEADER
    c.setStrokeColor(NAVY); c.setLineWidth(0.6)
    c.line(MARGIN_L, PAGE_H - 18 * mm, PAGE_W - MARGIN_R, PAGE_H - 18 * mm)
    baseline = PAGE_H - 15 * mm
    # Logo oficial de la plataforma, alineado a la izquierda del header.
    logo_h = 4.6 * mm
    logo_w = logo_h * LOGO_RATIO
    try:
        c.drawImage(str(LOGO), MARGIN_L, baseline - 1.2 * mm,
                    width=logo_w, height=logo_h, mask="auto",
                    preserveAspectRatio=True)
    except Exception:
        pass
    # Tagline centrada
    c.setFillColor(SLATE); c.setFont("Helvetica", 8)
    c.drawCentredString(PAGE_W / 2, baseline,
                        "Inteligencia operativa marítima y portuaria en tiempo real")
    # FOOTER
    c.setStrokeColor(SLATE_LIGHT); c.setLineWidth(0.3)
    c.line(MARGIN_L, 14 * mm, PAGE_W - MARGIN_R, 14 * mm)
    c.setFont("Helvetica", 8); c.setFillColor(SLATE)
    c.drawString(MARGIN_L, 9 * mm, "Presentación PortIO  ·  Confidencial")
    c.drawRightString(PAGE_W - MARGIN_R, 9 * mm, f"Página {doc.page}")
    c.restoreState()


# -----------------------------------------------------------------------------
# Diagrama de módulos
# -----------------------------------------------------------------------------

def diagram_modules() -> Drawing:
    """Tres módulos sobre una capa común de datos AIS en tiempo real."""
    H = 210
    d = Drawing(CONTENT_W, H)
    cw = CONTENT_W

    mods = [
        ("MARÍTIMO", "Visibilidad en", "tiempo real", NAVY),
        ("OPERATIVA", "Escalas, atraques", "y fondeo", NAVY_LIGHT),
        ("INTELIGENCIA IA", "Asistente y resumen", "ejecutivo diario", TEAL),
    ]
    gap = 18
    bx_w = (cw - gap * 2) / 3
    bx_h = 76
    bx_y = H - bx_h - 6
    for i, (name, l1, l2, col) in enumerate(mods):
        x = i * (bx_w + gap)
        d.add(Rect(x, bx_y, bx_w, bx_h, rx=6, ry=6,
                   fillColor=col, strokeColor=NAVY_DARK, strokeWidth=0.8))
        d.add(Rect(x, bx_y + bx_h - 5, bx_w, 5, fillColor=CYAN, strokeColor=None))
        d.add(String(x + bx_w / 2, bx_y + 48, name, textAnchor="middle",
                     fontName="Helvetica-Bold", fontSize=12, fillColor=WHITE))
        d.add(String(x + bx_w / 2, bx_y + 30, l1, textAnchor="middle",
                     fontName="Helvetica", fontSize=8.5, fillColor=CYAN_LIGHT))
        d.add(String(x + bx_w / 2, bx_y + 18, l2, textAnchor="middle",
                     fontName="Helvetica", fontSize=8.5, fillColor=CYAN_LIGHT))
        # conector hacia la capa de datos
        d.add(Line(x + bx_w / 2, bx_y, x + bx_w / 2, 54,
                   strokeColor=SLATE_LIGHT, strokeWidth=1))

    # Capa de datos común
    db_w = cw * 0.82
    db_x = (cw - db_w) / 2
    d.add(Rect(db_x, 8, db_w, 42, rx=6, ry=6,
               fillColor=SLATE_BG, strokeColor=NAVY_LIGHT, strokeWidth=1))
    d.add(String(cw / 2, 32, "CAPA DE DATOS EN TIEMPO REAL",
                 textAnchor="middle", fontName="Helvetica-Bold",
                 fontSize=10, fillColor=NAVY))
    d.add(String(cw / 2, 18, "AIS en vivo  ·  PCS  ·  WebSocket STOMP  ·  PostgreSQL + PostGIS  ·  multi-tenant",
                 textAnchor="middle", fontName="Helvetica", fontSize=8, fillColor=SLATE))
    return d


# -----------------------------------------------------------------------------
# Flowable helpers
# -----------------------------------------------------------------------------

def hr(width=1, color=NAVY) -> Drawing:
    d = Drawing(CONTENT_W, 6)
    d.add(Line(0, 3, CONTENT_W, 3, strokeColor=color, strokeWidth=width))
    return d


KPI_CARD_HEIGHT = 92
KPI_CARD_GAP = 18


def kpi_card(value: str, label: str, cell_w: float) -> Table:
    t = Table(
        [[Paragraph(value, ST_KPI_NUM)], [Paragraph(label, ST_KPI_LABEL)]],
        colWidths=[cell_w], rowHeights=[52, 32],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), NAVY),
        ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
        ("TOPPADDING", (0, 0), (0, 0), 10),
        ("BOTTOMPADDING", (0, 0), (0, 0), 10),
        ("BACKGROUND", (0, 1), (0, 1), WHITE),
        ("VALIGN", (0, 1), (0, 1), "MIDDLE"),
        ("TOPPADDING", (0, 1), (0, 1), 8),
        ("BOTTOMPADDING", (0, 1), (0, 1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.4, SLATE_LIGHT),
        ("LINEABOVE", (0, 0), (-1, 0), 2.5, CYAN),
    ]))
    return t


def kpi_row(items: list[tuple[str, str]]) -> Table:
    n = len(items)
    if n == 0:
        return Spacer(1, 0)
    total_gap = KPI_CARD_GAP * (n - 1)
    card_w = (CONTENT_W - total_gap) / n
    cols, widths = [], []
    for i, (v, l) in enumerate(items):
        cols.append(kpi_card(v, l, cell_w=card_w))
        widths.append(card_w)
        if i < n - 1:
            cols.append("")
            widths.append(KPI_CARD_GAP)
    t = Table([cols], colWidths=widths, rowHeights=[KPI_CARD_HEIGHT])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def std_table(header, rows, col_widths=None, first_col_bold=True):
    head = [Paragraph(h, ST_TABLE_HEAD) for h in header]
    body = []
    for r in rows:
        cells = []
        for i, cval in enumerate(r):
            style = ST_TABLE_CELL_BOLD if (first_col_bold and i == 0) else ST_TABLE_CELL
            cells.append(Paragraph(cval, style))
        body.append(cells)
    data = [head] + body
    cw = col_widths or [CONTENT_W / len(header)] * len(header)
    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SLATE_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, SLATE_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.6, NAVY_LIGHT),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def screenshot(filename, caption, value=None, width_frac=1.0):
    path = SCREENSHOTS / filename
    if not path.exists():
        return [Paragraph(f"<i>[Captura {filename} no disponible - ejecuta "
                          f"<b>npm run screenshot</b>]</i>", ST_CAPTION)]
    img = Image(str(path))
    img._restrictSize(CONTENT_W * width_frac, 17 * cm)
    img.hAlign = "CENTER"
    cap = [f"<b>{caption}</b>"]
    if value:
        cap.append(f"<font color=\"#003A8C\">Valor:</font> {value}")
    return [img, Paragraph("  -  ".join(cap), ST_CAPTION)]


def li(text):
    return Paragraph(f"• {text}", ST_LI)


def block_divider(label, title, subtitle, toc_text):
    return [
        TOCAnchor(0, toc_text),
        Spacer(1, 5 * cm),
        Paragraph(label, ST_BLOCK_LABEL),
        Paragraph(title, ST_BLOCK_TITLE),
        Spacer(1, 4 * mm),
        Paragraph(subtitle, ST_BODY_LEAD),
        Spacer(1, 8 * cm),
    ]


# -----------------------------------------------------------------------------
# TOC plumbing
# -----------------------------------------------------------------------------

class TOCAnchor(Flowable):
    """Flowable invisible que registra una entrada TOC sin ocupar espacio."""

    def __init__(self, level: int, text: str) -> None:
        super().__init__()
        self._level = level
        self._text = text
        self.width = 0
        self.height = 0

    def wrap(self, availWidth, availHeight):
        return (0, 0)

    def draw(self):
        pass


def open_sub_block(story_list, title):
    story_list.append(NextPageTemplate("content"))
    story_list.append(PageBreak())
    story_list.append(TOCAnchor(1, " ".join(title.split())))


class PortIODocTemplate(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, TOCAnchor):
            key = f"toc_anchor_{id(flowable)}"
            self.canv.bookmarkPage(key, fit="XYZ", top=PAGE_H, left=0, zoom=0)
            self.notify("TOCEntry", (flowable._level, flowable._text, self.page, key))


# -----------------------------------------------------------------------------
# Build
# -----------------------------------------------------------------------------

def build():
    doc = PortIODocTemplate(
        str(OUTPUT_PDF), pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=MARGIN_T, bottomMargin=MARGIN_B,
        title="Presentación PortIO - Inteligencia operativa marítima y portuaria",
        author="PortIO", subject="Presentación de plataforma",
    )

    cover_frame = Frame(28 * mm, 38 * mm, PAGE_W - 56 * mm, PAGE_H - 38 * mm,
                        id="cover", showBoundary=0,
                        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    divider_frame = Frame(PAGE_W * 0.42 + 12 * mm, MARGIN_B,
                          PAGE_W - PAGE_W * 0.42 - 12 * mm - MARGIN_R,
                          PAGE_H - MARGIN_T - MARGIN_B, id="div")
    content_frame = Frame(MARGIN_L, MARGIN_B, CONTENT_W,
                          PAGE_H - MARGIN_T - MARGIN_B - 4 * mm,
                          leftPadding=0, rightPadding=0, topPadding=4, bottomPadding=4,
                          id="content")
    doc.addPageTemplates([
        PageTemplate(id="cover",   frames=[cover_frame],   onPage=cover_background),
        PageTemplate(id="divider", frames=[divider_frame], onPage=divider_background),
        PageTemplate(id="content", frames=[content_frame], onPage=content_background),
    ])

    story: list = []
    _cover(story)
    _toc(story, doc)
    _resumen(story, doc)
    _bloque1(story, doc)
    _bloque2(story, doc)
    _bloque3(story, doc)
    _cierre(story, doc)

    doc.multiBuild(story)
    print(f"✓ Generado: {OUTPUT_PDF}")


def _cover(story):
    cover_title = ParagraphStyle("CoverTitle", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=86, leading=92,
        textColor=BLACK, alignment=TA_CENTER, spaceAfter=14)
    cover_subtitle = ParagraphStyle("CoverSubtitle", parent=styles["Normal"],
        fontName="Helvetica", fontSize=15, leading=21,
        textColor=SLATE, alignment=TA_CENTER, spaceAfter=18)
    cover_desc = ParagraphStyle("CoverDesc", parent=styles["Normal"],
        fontName="Helvetica", fontSize=11, leading=16,
        textColor=SLATE, alignment=TA_CENTER, spaceAfter=0,
        leftIndent=PAGE_W * 0.05, rightIndent=PAGE_W * 0.05)

    del cover_title  # el logo oficial sustituye al wordmark tipográfico

    inner = [
        logo_image(110 * mm),
        Spacer(1, 14 * mm),
        Paragraph("Inteligencia operativa marítima y portuaria en tiempo real",
                  cover_subtitle),
        Spacer(1, 6 * mm),
        Paragraph(
            "Una sola capa digital que reúne la visibilidad del tráfico marítimo, "
            "la planificación de escalas y atraques, y un asistente de IA sobre "
            "los datos reales del puerto - sobre datos AIS en vivo.",
            cover_desc),
        Spacer(1, 40 * mm),
    ]
    frame_h = PAGE_H - 38 * mm
    block = Table([[inner]], colWidths=[PAGE_W - 56 * mm], rowHeights=[frame_h])
    block.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(block)


def _toc(story, doc):
    story.append(NextPageTemplate("content"))
    story.append(PageBreak())
    story.append(Paragraph("Índice", ParagraphStyle(
        "IdxTitle", parent=ST_H1, fontSize=32, leading=36, spaceAfter=4)))
    story.append(hr(width=2, color=NAVY))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Presentación en tres bloques: visión general de la plataforma, recorrido "
        "por las pantallas de los tres módulos, y propuesta de valor para el puerto. "
        "Cada entrada del índice es navegable.",
        ParagraphStyle("IdxIntro", parent=ST_BODY, textColor=SLATE,
                       fontSize=10, leading=14, spaceAfter=10)))
    story.append(Spacer(1, 6 * mm))
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("TOC0", fontName="Helvetica-Bold", fontSize=12,
                       leading=22, textColor=NAVY, leftIndent=12, rightIndent=0,
                       spaceBefore=14, spaceAfter=10,
                       backColor=SLATE_BG, borderPadding=(6, 12, 6, 12)),
        ParagraphStyle("TOC1", fontName="Helvetica", fontSize=10,
                       leading=15, textColor=NAVY, leftIndent=28, rightIndent=8,
                       spaceBefore=6, spaceAfter=2),
    ]
    story.append(toc)


# ----- Resumen ejecutivo -----

def _resumen(story, doc):
    story.append(NextPageTemplate("content"))
    story.append(PageBreak())
    story.append(TOCAnchor(0, "Resumen ejecutivo"))
    story.append(Paragraph("Resumen ejecutivo", ST_H1))
    story.append(hr(width=2, color=NAVY))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph(
        "<b>PortIO</b> es la plataforma que da a un puerto una visión operativa "
        "única y en tiempo real: qué buques hay en el área, qué llega en las "
        "próximas horas, cómo se planifican muelles y escalas, y un asistente de "
        "IA que responde en lenguaje natural con los datos reales de todo ese "
        "tráfico. Toda la información parte de la misma fuente -el flujo AIS en "
        "vivo- y se presenta a cada usuario filtrada por su organización.",
        ST_BODY_LEAD))
    story.append(Spacer(1, 4 * mm))
    story.append(kpi_row([
        ("3", "Módulos integrados"),
        ("Tiempo real", "Posiciones vía WebSocket"),
        ("IA", "Asistente conversacional"),
        ("Streaming", "Resumen ejecutivo diario"),
    ]))
    story.append(Spacer(1, 8 * mm))
    story += screenshot("00-dashboard.png",
        "Panel de inicio - resumen de actividad del puerto en una sola vista",
        value="el operador entra y entiende el estado del puerto en segundos")


# ----- Bloque 1 · Visión general -----

def _bloque1(story, doc):
    story.append(NextPageTemplate("divider"))
    story.append(PageBreak())
    story += block_divider(
        "BLOQUE 1",
        'Visión<br/>general',
        "Qué es PortIO, qué necesidad cubre y cómo se organiza la plataforma.",
        toc_text="Visión general")

    open_sub_block(story, "Propósito")
    story.append(Paragraph("Propósito y necesidad", ST_H1))
    story.append(hr(width=2, color=NAVY))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Un puerto recibe en todo momento información de tráfico marítimo (AIS), "
        "pero esa información llega dispersa, sin contexto operativo y sin enlazar "
        "con la planificación de muelles ni con las obligaciones ambientales. El "
        "resultado: decisiones tardías, congestión imprevista y reporting manual.",
        ST_BODY))
    story.append(Paragraph(
        "<b>PortIO</b> convierte ese flujo en una capa operativa coherente. Sobre "
        "una misma base de datos en tiempo real construye tres módulos que se "
        "refuerzan entre sí:", ST_BODY))
    story.append(li("<b>Visibilidad</b>: ver en vivo quién está y qué llega."))
    story.append(li("<b>Decisión</b>: planificar escalas y atraques sobre esa visibilidad."))
    story.append(li("<b>Inteligencia</b>: preguntar en lenguaje natural y recibir respuestas sobre los datos reales."))
    story.append(Spacer(1, 6 * mm))
    story.append(std_table(
        header=["Necesidad del puerto", "Capacidad de PortIO"],
        rows=[
            ["Saber qué buques hay y qué llega",
             "Mapa en vivo + tabla de buques + predicción de ETA con nivel de confianza"],
            ["Anticipar congestión de muelles",
             "Previsión de ocupación a 72 h y alertas de conflicto de atraque"],
            ["Planificar escalas y asignar muelle",
             "CRUD de escalas con sugerencia automática de muelle puntuada"],
            ["Responder preguntas operativas sin navegar pantallas",
             "Asistente de IA que consulta los datos reales (nunca inventa cifras) y "
             "resumen ejecutivo diario generado automáticamente"],
        ],
        col_widths=[CONTENT_W * 0.42, CONTENT_W * 0.58]))

    open_sub_block(story, "Los tres módulos")
    story.append(Paragraph("Los tres módulos", ST_H1))
    story.append(hr(width=2, color=NAVY))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "La plataforma se organiza en tres módulos sobre una capa común de datos "
        "en tiempo real. Cada uno cubre una etapa del ciclo operativo: ver, "
        "decidir y rendir cuentas.", ST_BODY))
    story.append(Spacer(1, 4 * mm))
    story.append(diagram_modules())
    story.append(Spacer(1, 6 * mm))
    story.append(std_table(
        header=["Módulo", "Para qué sirve", "Pantallas"],
        rows=[
            ["Marítimo", "Visibilidad operacional en tiempo real del área portuaria",
             "Mapa, Buques en puerto, ETA, Alertas"],
            ["Operativa", "Planificación y gestión de escalas, muelles y fondeo",
             "KPIs, Fondeo, Atraques, Escalas"],
            ["Inteligencia Artificial", "Asistente conversacional sobre datos reales y resumen ejecutivo diario",
             "Asistente virtual, Resumen diario"],
        ],
        col_widths=[CONTENT_W * 0.18, CONTENT_W * 0.52, CONTENT_W * 0.30]))


# ----- Bloque 2 · Recorrido -----

def _screen(story, title, body, filename, caption, value=None, bullets=None):
    parts = [Paragraph(title, ST_H3), Paragraph(body, ST_BODY)]
    for b in (bullets or []):
        parts.append(li(b))
    story.append(KeepTogether(parts))
    story += screenshot(filename, caption, value=value)


def _bloque2(story, doc):
    story.append(NextPageTemplate("divider"))
    story.append(PageBreak())
    story += block_divider(
        "BLOQUE 2",
        "Recorrido por<br/>la plataforma",
        "Las diez pantallas de los tres módulos, con capturas reales de demo.portio.es.",
        toc_text="Recorrido por la plataforma")

    # --- Módulo Marítimo ---
    open_sub_block(story, "Módulo Marítimo")
    story.append(Paragraph("Módulo Marítimo", ST_H1))
    story.append(hr(width=2, color=NAVY))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "Da visibilidad en tiempo real sobre los buques presentes en el área "
        "portuaria. Es el módulo «operador de torre»: quién está, dónde, en qué "
        "estado y qué viene en las próximas horas.", ST_BODY_LEAD))
    story.append(Spacer(1, 3 * mm))

    _screen(story, "1 · Mapa de buques  ·  /buques",
        "Vista cartográfica en vivo del puerto. Cada buque se dibuja como un icono "
        "orientado a su rumbo, con casco a escala real para los grandes. Al pulsar "
        "un buque se abre el detalle estático (eslora, IMO, tipo, propietario, ETA).",
        "01-mapa-buques.png",
        "Mapa de buques en vivo sobre el Port de Tarragona",
        value="el operador ve de un vistazo la situación real del puerto")

    _screen(story, "2 · Buques en puerto  ·  /buques/puerto",
        "Tabla ordenable y filtrable de todos los buques del área, con KPIs resumen "
        "arriba (totales por estado y velocidad media). Pensada para el operador que "
        "prefiere una rejilla al mapa.",
        "02-buques-puerto.png",
        "Listado tabular de buques con filtros por estado, tipo y bandera",
        value="encontrar y filtrar buques sin depender del mapa")

    _screen(story, "3 · Predicción de ETA  ·  /buques/eta",
        "Qué llega pronto y con cuánta confianza. Compara la ETA declarada por el "
        "buque con la ETA recalculada desde AIS y muestra un nivel de confianza "
        "(alta / media / baja) según distancia y consistencia del rumbo.",
        "03-eta.png",
        "Llegadas previstas con ETA declarada vs. estimada y nivel de confianza",
        value="anticipar llegadas con una estimación independiente y fiable")

    _screen(story, "4 · Alertas y congestión  ·  /buques/alertas",
        "Dashboard de eventos operativos: entradas al área, ETAs actualizadas, "
        "muelles liberados y congestión prevista. Incluye una previsión de ocupación "
        "a 72 h por ventanas horarias con indicador visual de saturación.",
        "04-alertas-congestion.png",
        "Eventos operativos en vivo y previsión de congestión a 72 horas",
        value="reaccionar a tiempo y prever la saturación antes de que ocurra")

    # --- Módulo Operativa ---
    open_sub_block(story, "Módulo Operativa")
    story.append(Paragraph("Módulo Operativa", ST_H1))
    story.append(hr(width=2, color=NAVY))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "Gestión y planificación de escalas, muelles y fondeo. Aquí el operador "
        "deja de «ver» y empieza a «decidir»: crear escalas, asignar muelles y "
        "transicionar estados.", ST_BODY_LEAD))
    story.append(Spacer(1, 3 * mm))

    _screen(story, "5 · KPIs operativos  ·  /operativa",
        "Panel ejecutivo de un vistazo: buques activos, muelles ocupados/libres, "
        "alertas pendientes y conflictos de atraque. Incluye las próximas escalas y "
        "un resumen de alertas recientes.",
        "05-operativa-kpis.png",
        "Panel ejecutivo del estado operativo del puerto",
        value="medir el pulso operativo del puerto en una pantalla")

    _screen(story, "6 · Fondeo  ·  /operativa/fondeo",
        "Monitoriza los buques fondeados a la espera de muelle libre. Calcula el "
        "tiempo de espera acumulado por buque y separa los que ya tienen muelle "
        "asignado de los que no. Punto de coordinación entre agente y puerto.",
        "06-fondeo.png",
        "Buques en espera de muelle con tiempo de fondeo acumulado",
        value="coordinar la espera y reducir tiempos muertos en fondeo")

    _screen(story, "7 · Atraques  ·  /operativa/atraques",
        "Estado de cada muelle: quién lo ocupa, cuándo quedará libre y qué buque "
        "entra después. Marca en rojo los conflictos (el siguiente arribo es antes "
        "de la liberación estimada) e identifica muelles infrautilizados y saturados.",
        "07-atraques.png",
        "Estado y previsión de cada muelle, con conflictos resaltados",
        value="evitar choques de planificación y optimizar el uso de muelles")

    _screen(story, "8 · Planificación de escalas  ·  /operativa/escalas",
        "CRUD completo de escalas. El usuario crea escalas, las transiciona por su "
        "ciclo (programada → llegando → atracada → operaciones → saliendo → salida), "
        "asigna muelle y consulta sugerencias automáticas puntuadas por eslora, "
        "calado, tipo y disponibilidad.",
        "08-escalas.png",
        "Gestión del ciclo de vida completo de una escala con sugerencia de muelle",
        value="planificar escalas con apoyo de sugerencias automáticas")

    # --- Módulo Inteligencia Artificial ---
    open_sub_block(story, "Módulo Inteligencia Artificial")
    story.append(Paragraph("Módulo Inteligencia Artificial", ST_H1))
    story.append(hr(width=2, color=NAVY))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "Un asistente conversacional sobre los datos operativos reales del puerto, "
        "más un resumen ejecutivo diario generado automáticamente. El modelo nunca "
        "inventa cifras: las preguntas sobre el sistema se resuelven consultando "
        "los datos reales mediante herramientas dedicadas, no por aproximación.",
        ST_BODY_LEAD))
    story.append(Spacer(1, 3 * mm))

    _screen(story, "9 · Asistente virtual  ·  /asistente-virtual",
        "Chat a pantalla completa con historial de conversaciones persistente. "
        "El operador pregunta en lenguaje natural por escalas, atraques, alertas o "
        "buques, o por cómo usar la aplicación. La respuesta llega en streaming, "
        "token a token, con reconexión automática si se recarga la página a media "
        "respuesta.",
        "09-asistente-virtual.png",
        "Asistente conversacional respondiendo con datos operativos reales",
        value="resolver una pregunta operativa sin navegar ninguna pantalla")

    _screen(story, "10 · Resumen ejecutivo diario  ·  /resumen-diario",
        "Lectura ejecutiva de la actividad del día -escalas abiertas, cierres de "
        "hoy, alertas sin reconocer, ocupación de atraques- convertida en una "
        "narrativa breve en español, generada bajo demanda. Los datos se calculan "
        "primero y el modelo solo redacta la narrativa sobre ese bloque fijo: la "
        "cifra nunca puede divergir del texto.",
        "10-resumen-diario.png",
        "Resumen ejecutivo diario generado automáticamente",
        value="el responsable de turno entiende el día en una lectura de segundos")


# ----- Bloque 3 · Valor -----

def _bloque3(story, doc):
    story.append(NextPageTemplate("divider"))
    story.append(PageBreak())
    story += block_divider(
        "BLOQUE 3",
        "Valor para<br/>el puerto",
        "Por qué PortIO posiciona al puerto como Smart Port y refuerza su sostenibilidad.",
        toc_text="Valor para el puerto")

    open_sub_block(story, "Propuesta de valor")
    story.append(Paragraph("Propuesta de valor", ST_H1))
    story.append(hr(width=2, color=NAVY))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "PortIO no es una herramienta aislada: es la capa de inteligencia operativa "
        "que conecta lo que el puerto ya recibe (tráfico AIS) con lo que necesita "
        "decidir y reportar. Su valor está en la integración.", ST_BODY_LEAD))

    story.append(Paragraph("Tiempo real, no informes de ayer", ST_H3))
    story.append(Paragraph(
        "La posición de los buques llega por WebSocket y se refleja en el mapa y en "
        "los KPIs sin recargar. Las decisiones se toman sobre el estado actual del "
        "puerto, no sobre una foto antigua.", ST_BODY))

    story.append(Paragraph("Posicionamiento Smart Port", ST_H3))
    story.append(Paragraph(
        "Reunir visibilidad, planificación e inteligencia artificial en una sola "
        "plataforma digital es exactamente el tipo de capacidad que define a un "
        "puerto inteligente: datos que se convierten en decisiones, sin fricción.",
        ST_BODY))

    story.append(Paragraph("Respuestas, no paneles que interpretar", ST_H3))
    story.append(Paragraph(
        "El asistente de IA no sustituye los paneles operativos: los complementa. "
        "Un responsable de turno pregunta en lenguaje natural y recibe la "
        "respuesta apoyada en los datos reales del sistema -nunca una cifra "
        "generada por el modelo-, o el resumen ejecutivo del día sin tener que "
        "recorrer cada pantalla.", ST_BODY))
    story.append(Spacer(1, 4 * mm))

    story.append(std_table(
        header=["Antes", "Con PortIO"],
        rows=[
            ["AIS disperso y sin contexto operativo",
             "Una capa única en vivo: mapa, tablas y KPIs sobre la misma fuente"],
            ["Congestión que se descubre cuando ya ocurre",
             "Previsión de ocupación a 72 h y alertas de conflicto anticipadas"],
            ["Planificación de muelles en hojas de cálculo",
             "Escalas con ciclo de estados y sugerencia automática de muelle"],
            ["Recorrer cada pantalla para entender el estado del puerto",
             "Preguntar en lenguaje natural o leer el resumen ejecutivo diario"],
        ],
        col_widths=[CONTENT_W * 0.42, CONTENT_W * 0.58]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        "«Ver, decidir y preguntar sobre la misma información, en tiempo real.»",
        ST_QUOTE))

    open_sub_block(story, "API abierta")
    story.append(Paragraph("API abierta", ST_H1))
    story.append(hr(width=2, color=NAVY))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "PortIO publica sus datos de buques como una <b>API REST de solo lectura</b>, "
        "para que el puerto y su ecosistema -Autoridad Portuaria, dashboards "
        "corporativos y el Port Community System (PCS)- los integren en sus propios "
        "sistemas sin duplicar la fuente ni esperar a un informe.",
        ST_BODY_LEAD))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "La integración cubre dos recursos: el <b>detalle de cada buque</b> y su "
        "<b>historial</b>.", ST_BODY))
    story.append(Spacer(1, 4 * mm))
    story.append(std_table(
        header=["Recurso", "Qué entrega"],
        rows=[
            ["Detalle de buque",
             "Ficha de cada buque: identificación (MMSI / IMO), nombre, tipo, "
             "eslora y tonelaje bruto/de peso muerto"],
            ["Historial de buques",
             "Volumen de registros AIS acumulados por buque, consultable para un "
             "buque concreto filtrando por IMO o MMSI"],
        ],
        col_widths=[CONTENT_W * 0.30, CONTENT_W * 0.70]))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("Cómo se consume", ST_H3))
    story.append(li("<b>REST sobre HTTPS y respuesta JSON</b>, lista para cualquier "
                    "lenguaje (cURL, Python, JavaScript, PHP, Java)."))
    story.append(li("<b>Solo lectura</b>: la API consulta datos, nunca los modifica."))
    story.append(li("<b>Clave por organización</b>: cada petición se autentica con la "
                    "API key de la entidad en la cabecera <font face=\"Courier\">X-API-Key</font>; "
                    "el administrador la genera y puede regenerarla, lo que invalida la "
                    "anterior al instante."))
    story.append(li("<b>Contrato estable y filtrable</b>: versionado para no romper a "
                    "los integradores, con consultas por buque (IMO o MMSI)."))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "<b>Control de acceso.</b> La API es de solo lectura y expone únicamente "
        "metadatos de buques e historial -nunca datos operativos o comerciales del "
        "puerto-. La pasarela aplica CORS y un límite de uso (100 peticiones por "
        "minuto y origen) para proteger la plataforma frente a picos de tráfico.",
        ST_NOTE))


def _cierre(story, doc):
    story.append(NextPageTemplate("content"))
    story.append(PageBreak())
    story.append(Spacer(1, 4 * cm))
    story.append(logo_image(80 * mm))
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph(
        "Inteligencia operativa marítima y portuaria en tiempo real",
        ParagraphStyle("EndSub", parent=styles["Normal"], fontName="Helvetica",
                       fontSize=12, leading=18, textColor=SLATE, alignment=TA_CENTER,
                       spaceAfter=20)))
    story.append(hr(width=1.5, color=CYAN))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        "demo.portio.es",
        ParagraphStyle("EndUrl", parent=styles["Normal"], fontName="Helvetica-Bold",
                       fontSize=12, textColor=NAVY, alignment=TA_CENTER)))


if __name__ == "__main__":
    build()
