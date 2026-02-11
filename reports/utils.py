import csv
import os
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from datetime import datetime
from .converter import convert

def _register_fonts():
    """Register fonts for PDF."""
    # Try multiple possible locations
    font_dirs = []
    if getattr(settings, 'STATIC_ROOT', None):
        font_dirs.append(os.path.join(settings.STATIC_ROOT, 'fonts'))
    font_dirs.append(os.path.join(settings.BASE_DIR, 'static', 'fonts'))
    
    regular_font = 'Helvetica'
    bold_font = 'Helvetica-Bold'
    
    font_found = False
    
    for font_dir in font_dirs:
        if not os.path.exists(font_dir):
            continue
            
        # Try to register Zawgyi (mmrtext) for correct rendering after conversion
        zg_reg_path = os.path.join(font_dir, 'mmrtext.ttf')
        zg_bold_path = os.path.join(font_dir, 'mmrtextb.ttf')
        
        if os.path.exists(zg_reg_path):
            try:
                zg_font = 'Zawgyi-One'
                zg_font_bold = 'Zawgyi-One-Bold'
                pdfmetrics.registerFont(TTFont(zg_font, zg_reg_path))
                if os.path.exists(zg_bold_path):
                    pdfmetrics.registerFont(TTFont(zg_font_bold, zg_bold_path))
                else:
                    zg_font_bold = zg_font
                
                regular_font = zg_font
                bold_font = zg_font_bold
                font_found = True
                # Prefer Zawgyi if found because we use converter
                break 
            except Exception as e:
                print(f"Error registering Zawgyi from {font_dir}: {e}")

        # Fallback/Alternative: Pyidaungsu
        reg_path = os.path.join(font_dir, 'Pyidaungsu-Regular.ttf')
        bold_path = os.path.join(font_dir, 'Pyidaungsu-Bold.ttf')
        
        if os.path.exists(reg_path) and os.path.exists(bold_path) and not font_found:
            try:
                pdfmetrics.registerFont(TTFont('Pyidaungsu', reg_path))
                pdfmetrics.registerFont(TTFont('Pyidaungsu-Bold', bold_path))
                regular_font = 'Pyidaungsu'
                bold_font = 'Pyidaungsu-Bold'
                font_found = True
            except Exception as e:
                print(f"Error registering Pyidaungsu from {font_dir}: {e}")
                
    if not font_found:
        print("No Myanmar fonts found, falling back to Helvetica")
        
    return regular_font, bold_font

def _header_footer(canvas, doc):
    """Draw header and footer on each page."""
    canvas.saveState()
    
    # Fonts
    regular_font = 'Helvetica'
    bold_font = 'Helvetica-Bold'
    try:
        registered_fonts = pdfmetrics.getRegisteredFontNames()
        if 'Zawgyi-One' in registered_fonts:
            regular_font = 'Zawgyi-One'
            bold_font = 'Zawgyi-One-Bold'
        elif 'Pyidaungsu' in registered_fonts:
            regular_font = 'Pyidaungsu'
            bold_font = 'Pyidaungsu-Bold'
    except:
        pass

    # Company Info
    try:
        from master_data.models import CompanySetting
        company = CompanySetting.objects.first()
    except ImportError:
        company = None
    
    width, height = doc.pagesize
    
    # Logo
    if company and company.logo:
        try:
            if os.path.exists(company.logo.path):
                # Draw logo at top left
                canvas.drawImage(company.logo.path, 20*mm, height - 30*mm, width=20*mm, height=20*mm, preserveAspectRatio=True, mask='auto')
        except:
            pass

    # Company Name & Address (Center)
    y = height - 15*mm
    shop_name = company.shop_name if company and company.shop_name else ""
    # Convert shop name if needed
    if shop_name: shop_name = convert(shop_name)
    
    company_name = company.name if company else "Sales Distribution"
    if company_name: company_name = convert(company_name)
    
    canvas.setFont(bold_font, 14)
    if shop_name:
        canvas.drawCentredString(width / 2, y, shop_name)
        y -= 6*mm
        canvas.setFont(bold_font, 10)
        canvas.drawCentredString(width / 2, y, company_name)
    else:
        canvas.drawCentredString(width / 2, y, company_name)
    y -= 5*mm
    
    canvas.setFont(regular_font, 9)
    if company and company.address:
        canvas.drawCentredString(width / 2, y, convert(company.address))
        y -= 4*mm
    if company and company.phone:
        canvas.drawCentredString(width / 2, y, convert(company.phone))
        
    # Line
    canvas.setLineWidth(0.5)
    canvas.line(20*mm, height - 32*mm, width - 20*mm, height - 32*mm)
    
    # Footer
    canvas.setFont(regular_font, 8)
    canvas.drawString(20*mm, 10*mm, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    canvas.drawRightString(width - 20*mm, 10*mm, f"Page {doc.page}")
    
    canvas.restoreState()

def _export_csv(response, rows, headers):
    """Write rows to CSV in response."""
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(rows)
    return response


def _export_excel(response, rows, headers, sheet_name='Data'):
    """Write rows to Excel in response."""
    try:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name[:31]
        ws.append(headers)
        for row in rows:
            ws.append(row)
        wb.save(response)
        return response
    except ImportError:
        return None


def _export_pdf(response, rows, headers, title='Report', orientation='landscape'):
    """Write rows to PDF in response using ReportLab."""
    # Register fonts
    regular_font, bold_font = _register_fonts()
    
    # Convert data to Zawgyi (for rendering if Zawgyi font is used)
    # This handles the Unicode -> Zawgyi conversion for correct PDF rendering
    title = convert(title)
    headers = [convert(str(h)) for h in headers]
    rows = [[convert(str(cell)) if cell is not None else "" for cell in row] for row in rows]
    
    # Page setup
    pagesize = landscape(A4) if orientation == 'landscape' else A4
    width, height = pagesize
    left_margin = 20*mm
    right_margin = 20*mm
    
    doc = SimpleDocTemplate(
        response, 
        pagesize=pagesize,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=35*mm, # Make space for header
        bottomMargin=20*mm
    )
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontName=bold_font,
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 12))
    
    # Prepare data
    data = [headers] + rows
    
    # Calculate column widths
    avail_width = width - left_margin - right_margin
    
    # Heuristic for column weights
    weights = []
    for h in headers:
        h_lower = h.lower()
        if any(x in h_lower for x in ['item', 'product', 'description']):
            weights.append(3.5)
        elif any(x in h_lower for x in ['customer', 'name', 'remark']):
            weights.append(2.0)
        elif any(x in h_lower for x in ['date', 'time', 'status']):
            weights.append(1.2)
        elif any(x in h_lower for x in ['total', 'amount', 'price', 'cost', 'qty', '#']):
            weights.append(1.0)
        else:
            weights.append(1.0)
            
    total_weight = sum(weights)
    col_widths = [(w / total_weight) * avail_width for w in weights]
    
    # Create table
    t = Table(data, colWidths=col_widths, repeatRows=1)
    
    # Add style (Invoice-like clean design)
    style = TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), regular_font),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        
        # Header Style
        ('FONTNAME', (0, 0), (-1, 0), bold_font),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.black), # Thicker header line
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'), # Header text center
        
        # Row lines (horizontal only)
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.lightgrey),
        
        # No vertical grid (clean look)
    ])
    
    # Align numbers right
    for i, h in enumerate(headers):
        h_lower = h.lower()
        if any(x in h_lower for x in ['total', 'amount', 'price', 'cost', 'qty', 'quantity', 'balance', 'margin']):
            style.add('ALIGN', (i, 1), (i, -1), 'RIGHT')
        elif any(x in h_lower for x in ['date', 'status', '#']):
            style.add('ALIGN', (i, 1), (i, -1), 'CENTER')
        else:
            style.add('ALIGN', (i, 1), (i, -1), 'LEFT')
            
    t.setStyle(style)
    
    elements.append(t)
    doc.build(elements, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return response
