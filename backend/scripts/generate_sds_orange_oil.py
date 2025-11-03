#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera un SDS (Safety Data Sheet) dummy para OLA001 - C.P.ORANGE OIL ALD.1,20% MIN
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
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
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


def generate_sds_with_reportlab(output_path: Path):
    """Genera SDS usando reportlab (mejor calidad)"""
    doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#283593'),
        spaceAfter=10,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_JUSTIFY
    )
    
    # Encabezado de la SDS
    elements.append(Paragraph("SAFETY DATA SHEET - SDS", title_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Información de la empresa/producto
    company_info = [
        ['Product Name:', 'COLD PRESSED ORANGE OIL'],
        ['Product Code:', 'OLA001'],
        ['Description:', 'C.P.ORANGE OIL ALD.1,20% MIN'],
        ['CAS Number:', '8028-48-6'],
        ['Revision:', '3'],
        ['Date:', '11/02/2025'],
        ['Area:', 'Quality'],
        ['Page:', '3 de 10'],
    ]
    
    company_table = Table(company_info, colWidths=[2*inch, 4*inch])
    company_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(company_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Sección 3.1 Substances
    elements.append(Paragraph("3.1 Substances", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Tabla de composición química
    composition_data = [
        ['Chemical name', 'CAS No', 'Classification', 'Concentration (% w/w)'],
        ['D-Limonene', '5989-27-5', 
         'Flammable liquids, Category 3<br/>Acute toxicity (Oral), Category 5<br/>Skin irritation, Category 2<br/>Skin sensitization., Subcategory 1B<br/>Aspiration hazard., Category 1<br/>Dangerous to the aquatic environment – Acute, Category 1<br/>Dangerous to the aquatic environment – Chronic, Category 3',
         '>= 94 -< 99'],
        ['gamma-Terpinene', '99-85-4',
         'Flammable liquids, Category 3<br/>Acute toxicity (Oral), Category 5<br/>Reproductive toxicity, Category 2<br/>Aspiration hazard., Category 1<br/>Dangerous to the aquatic environment – Acute, Category 2<br/>Dangerous to the aquatic environment – Chronic, Category 2',
         '>= 0 -< 1'],
        ['Pin-2(3)-ene', '80-56-8',
         'Flammable liquids, Category 3<br/>Acute toxicity (Oral), Category 4<br/>Skin irritation, Category 2<br/>Skin sensitization., Category 1<br/>Aspiration hazard., Category 1<br/>Dangerous to the aquatic environment – Acute, Category 1<br/>Dangerous to the aquatic environment – Chronic, Category 1',
         '>= 0 -< 1'],
        ['Myrcene', '123-35-3',
         'Flammable liquids, Category 3<br/>Skin irritation, Category 2<br/>Eye irritation, Category 2A<br/>Skin sensitization., Category 1<br/>Aspiration hazard., Category 1<br/>Dangerous to the aquatic environment – Acute, Category 1<br/>Dangerous to the aquatic environment – Chronic, Category 2',
         '>= 1 -< 2.5'],
        ['Pin-2(10)-ene', '127-91-3',
         'Flammable liquids, Category 3<br/>Acute toxicity (Oral), Category 5<br/>Skin irritation, Category 2<br/>Skin sensitization., Category 1<br/>Aspiration hazard., Category 1<br/>Dangerous to the aquatic environment – Acute, Category 1<br/>Dangerous to the aquatic environment – Chronic, Category 1',
         '>= 0 -< 1'],
        ['Linalool', '78-70-6',
         'Flammable liquids, Category 4<br/>Acute toxicity (Oral), Category 5<br/>Skin irritation, Category 2<br/>Eye irritation, Category 2A<br/>Skin sensitization., Subcategory 1B',
         '>= 0 -< 1'],
    ]
    
    # Crear tabla con datos formateados
    comp_table = Table(composition_data, colWidths=[1.2*inch, 1*inch, 3*inch, 0.8*inch])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    elements.append(comp_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Información adicional sobre el producto
    elements.append(Paragraph("Product Information", heading_style))
    
    additional_info = [
        ['Appearance:', 'Clear, yellow to orange liquid'],
        ['Odor:', 'Characteristic orange, citrus'],
        ['Flash Point:', '> 60°C'],
        ['Boiling Point:', '176-178°C'],
        ['Specific Gravity:', '0.842 - 0.846 (20°C)'],
        ['Refractive Index:', '1.472 - 1.476 (20°C)'],
    ]
    
    info_table = Table(additional_info, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(info_table)
    
    # Build PDF
    doc.build(elements)
    print(f"✅ SDS generado exitosamente: {output_path}")


def generate_sds_with_pymupdf(output_path: Path):
    """Genera SDS usando PyMuPDF (alternativa si reportlab no está disponible)"""
    doc = fitz.open()  # Create new PDF
    page = doc.new_page(width=595, height=842)  # A4 size
    
    # Título
    title_rect = fitz.Rect(50, 50, 545, 100)
    # Calcular posición centrada manualmente
    title_text = "SAFETY DATA SHEET - SDS"
    title_bbox = fitz.Rect(50, 50, 545, 100)
    page.insert_text((297, 70), title_text, 
                     fontsize=18, color=(0.1, 0.14, 0.49))
    
    # Información del producto
    y_pos = 100
    product_info = [
        ("Product Name:", "COLD PRESSED ORANGE OIL"),
        ("Product Code:", "OLA001"),
        ("Description:", "C.P.ORANGE OIL ALD.1,20% MIN"),
        ("CAS Number:", "8028-48-6"),
        ("Revision:", "3"),
        ("Date:", "11/02/2025"),
    ]
    
    for label, value in product_info:
        page.insert_text((50, y_pos), f"{label}", fontsize=9, color=(0, 0, 0))
        page.insert_text((200, y_pos), f"{value}", fontsize=9, color=(0, 0, 0))
        y_pos += 18
    
    y_pos += 15
    
    # Sección 3.1 Substances
    page.insert_text((50, y_pos), "3.1 Substances", 
                     fontsize=12, color=(0.16, 0.21, 0.58))
    y_pos += 25
    
    # Encabezados de tabla
    header_data = [
        ("Chemical name", 50),
        ("CAS No", 200),
        ("Classification", 300),
        ("Concentration", 500),
    ]
    
    # Dibujar fondo para encabezados
    header_rect = fitz.Rect(50, y_pos - 12, 545, y_pos + 8)
    page.draw_rect(header_rect, color=(0.1, 0.14, 0.49), fill=(0.1, 0.14, 0.49))
    
    for text, x in header_data:
        page.insert_text((x, y_pos), text, fontsize=8, color=(1, 1, 1))
    y_pos += 20
    
    # Datos de composición
    composition_data = [
        ("D-Limonene", "5989-27-5", "Flammable liquids, Category 3; Acute toxicity (Oral), Category 5; Skin irritation, Category 2; Skin sensitization., Subcategory 1B; Aspiration hazard., Category 1; Dangerous to the aquatic environment – Acute, Category 1; Dangerous to the aquatic environment – Chronic, Category 3", ">= 94 -< 99"),
        ("gamma-Terpinene", "99-85-4", "Flammable liquids, Category 3; Acute toxicity (Oral), Category 5; Reproductive toxicity, Category 2; Aspiration hazard., Category 1; Dangerous to the aquatic environment – Acute, Category 2; Dangerous to the aquatic environment – Chronic, Category 2", ">= 0 -< 1"),
        ("Pin-2(3)-ene", "80-56-8", "Flammable liquids, Category 3; Acute toxicity (Oral), Category 4; Skin irritation, Category 2; Skin sensitization., Category 1; Aspiration hazard., Category 1; Dangerous to the aquatic environment – Acute, Category 1; Dangerous to the aquatic environment – Chronic, Category 1", ">= 0 -< 1"),
        ("Myrcene", "123-35-3", "Flammable liquids, Category 3; Skin irritation, Category 2; Eye irritation, Category 2A; Skin sensitization., Category 1; Aspiration hazard., Category 1; Dangerous to the aquatic environment – Acute, Category 1; Dangerous to the aquatic environment – Chronic, Category 2", ">= 1 -< 2.5"),
        ("Pin-2(10)-ene", "127-91-3", "Flammable liquids, Category 3; Acute toxicity (Oral), Category 5; Skin irritation, Category 2; Skin sensitization., Category 1; Aspiration hazard., Category 1; Dangerous to the aquatic environment – Acute, Category 1; Dangerous to the aquatic environment – Chronic, Category 1", ">= 0 -< 1"),
        ("Linalool", "78-70-6", "Flammable liquids, Category 4; Acute toxicity (Oral), Category 5; Skin irritation, Category 2; Eye irritation, Category 2A; Skin sensitization., Subcategory 1B", ">= 0 -< 1"),
    ]
    
    for i, (component, cas, classification, concentration) in enumerate(composition_data):
        bg_color = (0.96, 0.96, 0.96) if i % 2 == 0 else (1, 1, 1)
        row_rect = fitz.Rect(50, y_pos - 10, 545, y_pos + 25)
        page.draw_rect(row_rect, color=(0.8, 0.8, 0.8), fill=bg_color)
        
        # Component name
        page.insert_text((55, y_pos), component, fontsize=8, color=(0, 0, 0))
        # CAS number
        page.insert_text((205, y_pos), cas, fontsize=8, color=(0, 0, 0))
        # Classification (truncated if too long)
        classification_short = classification[:60] + "..." if len(classification) > 60 else classification
        page.insert_text((305, y_pos), classification_short, fontsize=7, color=(0, 0, 0))
        # Concentration
        page.insert_text((505, y_pos), concentration, fontsize=8, color=(0, 0, 0))
        
        y_pos += 30
    
    doc.save(str(output_path))
    doc.close()
    print(f"✅ SDS generado exitosamente: {output_path}")


def main():
    # Crear directorio de salida si no existe
    output_dir = Path(__file__).parent.parent.parent / "data" / "pdfs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "SDS_OLA001_Cold_Pressed_Orange_Oil.pdf"
    
    print("="*60)
    print("  📄 Generando SDS Dummy para OLA001 - Orange Oil")
    print("="*60)
    print(f"\n📁 Directorio de salida: {output_dir}")
    print(f"📄 Archivo: {output_path.name}\n")
    
    if REPORTLAB_AVAILABLE:
        print("✨ Usando reportlab (alta calidad)...")
        generate_sds_with_reportlab(output_path)
    elif PYMUPDF_AVAILABLE:
        print("✨ Usando PyMuPDF (calidad básica)...")
        generate_sds_with_pymupdf(output_path)
    else:
        print("❌ No hay librerías disponibles para generar PDF")
        sys.exit(1)
    
    print(f"\n✅ SDS generado exitosamente!")
    print(f"   Ubicación: {output_path}")
    print(f"\n💡 Puedes usar este archivo para:")
    print(f"   1. Subirlo en un cuestionario o línea azul")
    print(f"   2. El sistema extraerá automáticamente la composición química")
    print(f"   3. Se generará un composite Z1 con los componentes listados")


if __name__ == "__main__":
    main()

