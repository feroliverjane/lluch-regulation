#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera un TDS (Technical Data Sheet) dummy para Lavanda/Vainilla
con composición química que puede ser extraída por IA.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️  reportlab no disponible, usando PyMuPDF como alternativa...")

if not REPORTLAB_AVAILABLE:
    try:
        import fitz  # PyMuPDF
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False
        print("❌ Ni reportlab ni PyMuPDF disponibles. Instala reportlab: pip install reportlab")
        sys.exit(1)


def generate_tds_with_reportlab(output_path: Path):
    """Genera TDS usando reportlab (mejor calidad)"""
    doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#283593'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Título
    elements.append(Paragraph("TECHNICAL DATA SHEET", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Información del producto
    product_info = [
        ['Product Name:', 'Lavender Essential Oil (Lavandula angustifolia)'],
        ['Product Code:', 'LAVANDA9999'],
        ['CAS Number:', '8000-28-0'],
        ['INCI Name:', 'Lavandula Angustifolia (Lavender) Oil'],
        ['Date:', datetime.now().strftime('%Y-%m-%d')],
    ]
    
    product_table = Table(product_info, colWidths=[2*inch, 4*inch])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(product_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Composición química
    elements.append(Paragraph("CHEMICAL COMPOSITION", heading_style))
    
    composition_data = [
        ['Component Name', 'CAS Number', 'Percentage (%)'],
        ['Linalyl Acetate', '115-95-7', '35.5'],
        ['Linalool', '78-70-6', '28.3'],
        ['Camphor', '76-22-2', '12.7'],
        ['1,8-Cineole', '470-82-6', '8.9'],
        ['Terpinen-4-ol', '562-74-3', '4.2'],
        ['Lavandulyl Acetate', '25905-14-0', '3.1'],
        ['α-Terpineol', '98-55-5', '2.8'],
        ['Borneol', '507-70-0', '2.1'],
        ['Limonene', '138-86-3', '1.8'],
        ['Other Components', 'N/A', '1.4'],
    ]
    
    comp_table = Table(composition_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    elements.append(comp_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Propiedades físicas
    elements.append(Paragraph("PHYSICAL PROPERTIES", heading_style))
    
    properties_data = [
        ['Property', 'Value'],
        ['Appearance', 'Clear, colorless to pale yellow liquid'],
        ['Odor', 'Characteristic lavender, floral, herbaceous'],
        ['Specific Gravity (20°C)', '0.875 - 0.890'],
        ['Refractive Index (20°C)', '1.459 - 1.470'],
        ['Flash Point', '> 60°C'],
        ['Solubility', 'Soluble in ethanol, oils; Insoluble in water'],
    ]
    
    prop_table = Table(properties_data, colWidths=[2.5*inch, 4.5*inch])
    prop_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(prop_table)
    
    # Build PDF
    doc.build(elements)
    print(f"✅ TDS generado exitosamente: {output_path}")


def generate_tds_with_pymupdf(output_path: Path):
    """Genera TDS usando PyMuPDF (alternativa si reportlab no está disponible)"""
    doc = fitz.open()  # Create new PDF
    page = doc.new_page(width=595, height=842)  # A4 size
    
    # Título
    title_rect = fitz.Rect(50, 50, 545, 100)
    page.insert_text(title_rect.tl, "TECHNICAL DATA SHEET", 
                     fontsize=24, color=(0.1, 0.14, 0.49))
    
    # Información del producto
    y_pos = 120
    product_info = [
        ("Product Name:", "Lavender Essential Oil (Lavandula angustifolia)"),
        ("Product Code:", "LAVANDA9999"),
        ("CAS Number:", "8000-28-0"),
        ("INCI Name:", "Lavandula Angustifolia (Lavender) Oil"),
        ("Date:", datetime.now().strftime('%Y-%m-%d')),
    ]
    
    for label, value in product_info:
        page.insert_text((50, y_pos), f"{label}", fontsize=10, color=(0, 0, 0))
        page.insert_text((200, y_pos), f"{value}", fontsize=10, color=(0, 0, 0))
        y_pos += 20
    
    y_pos += 20
    
    # Composición química
    page.insert_text((50, y_pos), "CHEMICAL COMPOSITION", 
                     fontsize=14, color=(0.16, 0.21, 0.58))
    y_pos += 30
    
    # Encabezados de tabla
    page.insert_text((50, y_pos), "Component Name", fontsize=10, color=(1, 1, 1))
    page.insert_text((250, y_pos), "CAS Number", fontsize=10, color=(1, 1, 1))
    page.insert_text((400, y_pos), "Percentage (%)", fontsize=10, color=(1, 1, 1))
    
    # Dibujar fondo para encabezados
    header_rect = fitz.Rect(50, y_pos - 15, 545, y_pos + 5)
    page.draw_rect(header_rect, color=(0.1, 0.14, 0.49), fill=(0.1, 0.14, 0.49))
    y_pos += 25
    
    # Datos de composición
    composition_data = [
        ("Linalyl Acetate", "115-95-7", "35.5"),
        ("Linalool", "78-70-6", "28.3"),
        ("Camphor", "76-22-2", "12.7"),
        ("1,8-Cineole", "470-82-6", "8.9"),
        ("Terpinen-4-ol", "562-74-3", "4.2"),
        ("Lavandulyl Acetate", "25905-14-0", "3.1"),
        ("α-Terpineol", "98-55-5", "2.8"),
        ("Borneol", "507-70-0", "2.1"),
        ("Limonene", "138-86-3", "1.8"),
        ("Other Components", "N/A", "1.4"),
    ]
    
    for i, (component, cas, percentage) in enumerate(composition_data):
        bg_color = (0.96, 0.96, 0.96) if i % 2 == 0 else (1, 1, 1)
        row_rect = fitz.Rect(50, y_pos - 12, 545, y_pos + 8)
        page.draw_rect(row_rect, color=(0.8, 0.8, 0.8), fill=bg_color)
        
        page.insert_text((55, y_pos), component, fontsize=9, color=(0, 0, 0))
        page.insert_text((255, y_pos), cas, fontsize=9, color=(0, 0, 0))
        page.insert_text((405, y_pos), percentage, fontsize=9, color=(0, 0, 0))
        y_pos += 20
    
    doc.save(str(output_path))
    doc.close()
    print(f"✅ TDS generado exitosamente: {output_path}")


def main():
    # Crear directorio de salida si no existe
    output_dir = Path(__file__).parent.parent.parent / "data" / "pdfs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "TDS_LAVANDA9999_Lavender_Oil.pdf"
    
    print("="*60)
    print("  📄 Generando TDS Dummy para Lavanda/Vainilla")
    print("="*60)
    print(f"\n📁 Directorio de salida: {output_dir}")
    print(f"📄 Archivo: {output_path.name}\n")
    
    if REPORTLAB_AVAILABLE:
        print("✨ Usando reportlab (alta calidad)...")
        generate_tds_with_reportlab(output_path)
    elif PYMUPDF_AVAILABLE:
        print("✨ Usando PyMuPDF (calidad básica)...")
        generate_tds_with_pymupdf(output_path)
    else:
        print("❌ No hay librerías disponibles para generar PDF")
        sys.exit(1)
    
    print(f"\n✅ TDS generado exitosamente!")
    print(f"   Ubicación: {output_path}")
    print(f"\n💡 Puedes usar este archivo para:")
    print(f"   1. Subirlo en la línea azul de lavanda")
    print(f"   2. El sistema extraerá automáticamente la composición química")


if __name__ == "__main__":
    main()



