"""
Payment voucher and Invoice views and PDF generation.
"""
import os
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from orders.models import Payment, SalesOrder
from master_data.models import CompanySetting

def _register_fonts():
    """Register fonts for PDF."""
    font_dir = os.path.join(settings.STATIC_ROOT, 'fonts') if settings.STATIC_ROOT else os.path.join(settings.BASE_DIR, 'static', 'fonts')
    # Fallback if static root not set or fonts not there
    if not os.path.exists(font_dir):
         font_dir = os.path.join(settings.BASE_DIR, 'static', 'fonts')

    regular_font = 'Pyidaungsu'
    bold_font = 'Pyidaungsu-Bold'
    
    try:
        # Check if font files exist before registering
        if os.path.exists(os.path.join(font_dir, 'Pyidaungsu-Regular.ttf')):
            pdfmetrics.registerFont(TTFont(regular_font, os.path.join(font_dir, 'Pyidaungsu-Regular.ttf')))
            pdfmetrics.registerFont(TTFont(bold_font, os.path.join(font_dir, 'Pyidaungsu-Bold.ttf')))
        else:
            regular_font = 'Helvetica'
            bold_font = 'Helvetica-Bold'
    except Exception as e:
        # Fallback to standard fonts if custom fonts fail
        print(f"Font loading error: {e}")
        regular_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'
        
    return regular_font, bold_font

def _draw_voucher_header(pdf_canvas, width, height, company, font_regular, font_bold, title="PAYMENT VOUCHER"):
    """Draw PDF voucher header with company info and title."""
    # Company Info (Center)
    y = height - 40
    
    # Draw Logo if exists
    if company and company.logo:
        try:
            logo_path = company.logo.path
            if os.path.exists(logo_path):
                # Draw logo at top left
                pdf_canvas.drawImage(logo_path, 50, height - 100, width=80, height=80, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error drawing logo: {e}")

    company_name = company.name if company else "Sales Distribution"
    address = company.address if company else ""
    phone = company.phone if company else ""

    pdf_canvas.setFont(font_bold, 16)
    pdf_canvas.drawCentredString(width / 2, y, company_name)
    y -= 20

    pdf_canvas.setFont(font_regular, 10)
    if address:
        pdf_canvas.drawCentredString(width / 2, y, address)
        y -= 15
    if phone:
        pdf_canvas.drawCentredString(width / 2, y, phone)
        y -= 25

    # Title
    pdf_canvas.setFont(font_bold, 18)
    pdf_canvas.drawCentredString(width / 2, y, title)
    
    # Line below header
    y -= 10
    pdf_canvas.setLineWidth(1)
    pdf_canvas.line(50, y, width - 50, y)
    
    return y - 30

def _draw_voucher_meta(pdf_canvas, payment, width, y, font_regular, font_bold):
    pdf_canvas.setFont(font_regular, 10)
    
    # Left side
    pdf_canvas.drawString(50, y, f"Voucher No: {payment.voucher_number}")
    pdf_canvas.drawString(50, y - 15, f"Date: {payment.payment_date.strftime('%d-%m-%Y')}")
    
    # Right side
    payment_method_name = payment.payment_method.name_en if payment.payment_method else '-'
    pdf_canvas.drawRightString(width - 50, y, f"Ref No: {payment.reference_number or '-'}")
    pdf_canvas.drawRightString(width - 50, y - 15, f"Method: {payment_method_name}")
    
    return y - 40

def _draw_invoice_meta(pdf_canvas, order, width, y, font_regular, font_bold):
    """Draw invoice number, date, due date."""
    pdf_canvas.setFont(font_regular, 10)
    
    # Left side
    pdf_canvas.drawString(50, y, f"Invoice No: {order.order_number}")
    pdf_canvas.drawString(50, y - 15, f"Date: {order.order_date.strftime('%d-%m-%Y')}")
    
    # Right side
    status_text = order.get_status_display_my() if hasattr(order, 'get_status_display_my') else (order.status.name_en if order.status else '-')
    pdf_canvas.drawRightString(width - 50, y, f"Status: {status_text}")
    if order.delivery_date:
        pdf_canvas.drawRightString(width - 50, y - 15, f"Delivery: {order.delivery_date.strftime('%d-%m-%Y')}")
    
    return y - 40

def _draw_info_boxes(pdf_canvas, payment, width, y, font_regular, font_bold):
    # Customer Details Box
    box_width = (width - 120) / 2
    box_height = 80
    
    # Customer
    pdf_canvas.rect(50, y - box_height, box_width, box_height)
    pdf_canvas.setFont(font_bold, 10)
    pdf_canvas.drawString(60, y - 15, "Customer Details")
    pdf_canvas.line(50, y - 20, 50 + box_width, y - 20)
    
    pdf_canvas.setFont(font_regular, 9)
    pdf_canvas.drawString(60, y - 35, f"Name: {payment.order.customer.name}")
    pdf_canvas.drawString(60, y - 50, f"Phone: {payment.order.customer.phone}")
    
    # Order Details Box
    x2 = 50 + box_width + 20
    pdf_canvas.rect(x2, y - box_height, box_width, box_height)
    pdf_canvas.setFont(font_bold, 10)
    pdf_canvas.drawString(x2 + 10, y - 15, "Order Details")
    pdf_canvas.line(x2, y - 20, x2 + box_width, y - 20)
    
    pdf_canvas.setFont(font_regular, 9)
    pdf_canvas.drawString(x2 + 10, y - 35, f"Order No: {payment.order.order_number}")
    pdf_canvas.drawString(x2 + 10, y - 50, f"Total: {payment.order.total_amount:,.0f}")
    
    return y - box_height - 30

def _draw_amount_box(pdf_canvas, payment, width, y, font_regular, font_bold):
    extra_height = 25 if payment.notes else 0
    box_height = 80 + extra_height

    pdf_canvas.setLineWidth(0.5)
    pdf_canvas.setStrokeColor(colors.lightgrey)
    pdf_canvas.setDash([2, 2], 0)
    pdf_canvas.roundRect(50, y - box_height, width - 100, box_height, 5, stroke=1, fill=0)
    pdf_canvas.setDash([], 0)
    
    pdf_canvas.setFillColor(colors.gray)
    pdf_canvas.setFont(font_regular, 9)
    pdf_canvas.drawCentredString(width / 2, y - 20, "Amount Received")
    
    pdf_canvas.setFillColor(colors.black)
    pdf_canvas.setFont(font_bold, 18)
    
    # Add Payment Method and Amount combined
    payment_method_name = payment.payment_method.name_en if payment.payment_method else '-'
    pdf_canvas.drawCentredString(width / 2, y - 45, f"{payment_method_name} - {payment.amount:,.2f} Ks")
    
    if payment.notes:
        pdf_canvas.setFont(font_regular, 9)
        pdf_canvas.setFillColor(colors.gray)
        pdf_canvas.drawCentredString(width / 2, y - 70, f'"{payment.notes}"')

    return y - box_height - 60

def _draw_voucher_signatures(pdf_canvas, width, y, font_regular, font_bold):
    # Received By
    pdf_canvas.line(50, y, 200, y)
    pdf_canvas.setFont(font_regular, 10)
    pdf_canvas.drawCentredString(125, y - 15, "Received By")
    
    # Authorized By
    pdf_canvas.line(width - 200, y, width - 50, y)
    pdf_canvas.drawCentredString(width - 125, y - 15, "Authorized By")

def _draw_footer(pdf_canvas, width, text, font_regular, generated_at=None):
    if generated_at:
        pdf_canvas.setFont(font_regular, 8)
        pdf_canvas.setFillColor(colors.gray)
        # Convert to local time
        local_dt = timezone.localtime(generated_at)
        date_str = local_dt.strftime('%d-%m-%Y %H:%M')
        pdf_canvas.drawCentredString(width / 2, 20, f"Generated on {date_str}")

    if not text:
        text = "Thank you for your business!"
    
    pdf_canvas.setFont(font_regular, 9)
    pdf_canvas.setFillColor(colors.gray)
    
    # Handle multi-line footer text
    lines = text.split('\n')
    y = 40 # Bottom margin
    
    for line in reversed(lines):
        pdf_canvas.drawCentredString(width / 2, y, line.strip())
        y += 12

def _draw_invoice_items(pdf_canvas, order, width, y, font_regular, font_bold):
    data = [['Product', 'Qty', 'Price', 'Total']]
    for item in order.orderitem_set.all():
        data.append([
            item.product.name,
            str(item.quantity),
            f"{item.unit_price:,.0f}",
            f"{item.total_price:,.0f}"
        ])
    
    data.append(['', '', 'Subtotal:', f"{order.subtotal:,.0f}"])
    if order.discount_amount > 0:
        data.append(['', '', 'Discount:', f"-{order.discount_amount:,.0f}"])
    if order.delivery_fee > 0:
        data.append(['', '', 'Delivery:', f"{order.delivery_fee:,.0f}"])
    
    data.append(['', '', 'TOTAL:', f"{order.total_amount:,.0f}"])

    col_widths = [width * 0.4, width * 0.15, width * 0.2, width * 0.25]
    
    table = Table(data, colWidths=col_widths)
    
    style = [
        ('FONTNAME', (0, 0), (-1, -1), font_regular),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('LINEABOVE', (-2, -1), (-1, -1), 1, colors.black),
        ('FONTNAME', (-2, -1), (-1, -1), font_bold),
    ]
    
    table.setStyle(TableStyle(style))
    w, h = table.wrap(width, y)
    table.drawOn(pdf_canvas, 50, y - h)
    return y - h - 30

@login_required
def payment_voucher(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    company_setting = CompanySetting.objects.first()
    context = {
        'payment': payment,
        'company_setting': company_setting,
        'title': _('Payment Voucher'),
    }
    return render(request, 'orders/payment_voucher.html', context)

@login_required
def payment_voucher_pdf(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="voucher_{payment.voucher_number}.pdf"'
    
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    font_regular, font_bold = _register_fonts()
    company = CompanySetting.objects.first()
    
    y = _draw_voucher_header(p, width, height, company, font_regular, font_bold)
    y = _draw_voucher_meta(p, payment, width, y, font_regular, font_bold)
    y = _draw_info_boxes(p, payment, width, y, font_regular, font_bold)
    y = _draw_amount_box(p, payment, width, y, font_regular, font_bold)
    _draw_voucher_signatures(p, width, 100, font_regular, font_bold)
    
    # Footer
    footer_text = company.footer_text if company else None
    _draw_footer(p, width, footer_text, font_regular, generated_at=payment.created_at)
    
    p.showPage()
    p.save()
    return response

@login_required
def invoice_pdf(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="invoice_{order.order_number}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    font_regular, font_bold = _register_fonts()
    company = CompanySetting.objects.first()
    
    y = _draw_voucher_header(p, width, height, company, font_regular, font_bold, title="INVOICE")
    y = _draw_invoice_meta(p, order, width, y, font_regular, font_bold)
    
    # Bill To
    p.setFont(font_bold, 10)
    p.drawString(50, y, "Bill To:")
    p.setFont(font_regular, 10)
    p.drawString(50, y - 15, order.customer.name)
    if order.customer.phone:
        p.drawString(50, y - 30, order.customer.phone)
    if order.customer.street_address:
        p.drawString(50, y - 45, order.customer.street_address[:50])
        
    y -= 60
    
    y = _draw_invoice_items(p, order, width - 100, y, font_regular, font_bold)
    _draw_voucher_signatures(p, width, 100, font_regular, font_bold)
    
    # Footer
    footer_text = company.footer_text if company else None
    _draw_footer(p, width, footer_text, font_regular, generated_at=None)
    
    p.showPage()
    p.save()
    return response

@login_required
def invoice_view(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)
    company = CompanySetting.objects.first()
    context = {
        'title': _('Invoice'),
        'order': order,
        'company': company,
    }
    return render(request, 'orders/invoice.html', context)
