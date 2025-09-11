"""
Generator PDF dla raportu - moduł do konwersji raportu na PDF
"""

import base64
import io
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.colors import HexColor, black, blue, red, green
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re
import os


def _register_polish_fonts():
    """Rejestruje czcionki obsługujące polskie znaki"""
    try:
        # Próbuj zarejestrować DejaVu Sans (często dostępna w systemie)
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/dejavu/DejaVuSans.ttf',
            '/System/Library/Fonts/Arial.ttf',  # macOS
            'C:\\Windows\\Fonts\\arial.ttf',    # Windows
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf'
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('PolishFont', font_path))
                    pdfmetrics.registerFont(TTFont('PolishFontBold', font_path))
                    return True
                except:
                    continue
        
        # Jeśli nie znaleziono żadnej czcionki, użyj domyślnej
        print("⚠️ Nie znaleziono czcionki z polskimi znakami, używam domyślnej")
        return False
        
    except Exception as e:
        print(f"⚠️ Błąd rejestracji czcionki: {e}")
        return False


def generate_pdf_report(
    report_text: str,
    charts: Dict[str, str],
    business_domain: str,
    target_column: str
) -> bytes:
    """
    Generuje raport w formacie PDF
    
    Args:
        report_text: Tekst raportu w formacie markdown
        charts: Słownik z wykresami w formacie base64
        business_domain: Domena biznesowa
        target_column: Kolumna docelowa
        
    Returns:
        bytes: PDF jako bajty
    """
    
    # Zarejestruj czcionki z polskimi znakami
    has_polish_font = _register_polish_fonts()
    
    # Stwórz buffer dla PDF
    buffer = io.BytesIO()
    
    # Stwórz dokument PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Pobierz style
    styles = getSampleStyleSheet()
    
    # Wybierz czcionkę (polską lub domyślną)
    font_name = 'PolishFont' if has_polish_font else 'Helvetica'
    bold_font_name = 'PolishFontBold' if has_polish_font else 'Helvetica-Bold'
    
    # Stwórz custom style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=bold_font_name,
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=HexColor('#2E86AB')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=bold_font_name,
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor=HexColor('#A23B72')
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontName=bold_font_name,
        fontSize=14,
        spaceAfter=8,
        spaceBefore=12,
        textColor=HexColor('#F18F01')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        spaceAfter=6,
        alignment=TA_JUSTIFY
    )
    
    # Lista elementów do dodania do PDF
    story = []
    
    # Tytuł
    title = f"Raport Analizy Danych<br/>{business_domain}"
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 20))
    
    # Informacje podstawowe
    story.append(Paragraph("Informacje Podstawowe", heading_style))
    story.append(Paragraph(f"<b>Domena biznesowa:</b> {business_domain}", normal_style))
    story.append(Paragraph(f"<b>Kolumna docelowa:</b> {target_column}", normal_style))
    story.append(Spacer(1, 20))
    
    # Parsuj i dodaj tekst raportu
    _add_report_text_to_pdf(story, report_text, heading_style, subheading_style, normal_style)
    
    # Dodaj wykresy
    if charts:
        story.append(PageBreak())
        story.append(Paragraph("Wykresy i Wizualizacje", heading_style))
        story.append(Spacer(1, 20))
        
        _add_charts_to_pdf(story, charts, subheading_style)
    
    # Zbuduj PDF
    doc.build(story)
    
    # Pobierz PDF jako bajty
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


def _add_report_text_to_pdf(story, report_text, heading_style, subheading_style, normal_style):
    """Dodaje tekst raportu do PDF"""
    
    # Podziel tekst na linie
    lines = report_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 6))
            continue
        
        # Sprawdź czy to nagłówek
        if line.startswith('# '):
            # Główny tytuł
            title = line[2:].strip()
            story.append(Paragraph(title, heading_style))
            
        elif line.startswith('## '):
            # Nagłówek sekcji
            heading = line[3:].strip()
            story.append(Paragraph(heading, heading_style))
            
        elif line.startswith('### '):
            # Podnagłówek
            subheading = line[4:].strip()
            story.append(Paragraph(subheading, subheading_style))
            
        elif line.startswith('#### '):
            # Podnagłówek 4 poziomu
            subheading = line[5:].strip()
            story.append(Paragraph(subheading, subheading_style))
            
        elif line.startswith('- ') or line.startswith('* '):
            # Lista punktowana
            item = line[2:].strip()
            story.append(Paragraph(f"• {item}", normal_style))
            
        elif line.startswith('1. ') or line.startswith('2. ') or line.startswith('3. '):
            # Lista numerowana
            story.append(Paragraph(line, normal_style))
            
        elif line.startswith('**') and line.endswith('**'):
            # Tekst pogrubiony
            bold_text = line[2:-2].strip()
            story.append(Paragraph(f"<b>{bold_text}</b>", normal_style))
            
        else:
            # Zwykły tekst
            if line:
                # Konwertuj markdown na HTML dla reportlab z obsługą polskich znaków
                formatted_line = _convert_markdown_to_html(line)
                # Upewnij się, że polskie znaki są poprawnie obsłużone
                formatted_line = formatted_line.replace('ą', 'ą').replace('ć', 'ć').replace('ę', 'ę').replace('ł', 'ł').replace('ń', 'ń').replace('ó', 'ó').replace('ś', 'ś').replace('ź', 'ź').replace('ż', 'ż')
                formatted_line = formatted_line.replace('Ą', 'Ą').replace('Ć', 'Ć').replace('Ę', 'Ę').replace('Ł', 'Ł').replace('Ń', 'Ń').replace('Ó', 'Ó').replace('Ś', 'Ś').replace('Ź', 'Ź').replace('Ż', 'Ż')
                story.append(Paragraph(formatted_line, normal_style))


def _add_charts_to_pdf(story, charts, subheading_style):
    """Dodaje wykresy do PDF"""
    
    chart_titles = {
        'temporal_trends': '📈 Trendy Czasowe',
        'feature_importance': '🎯 Ważność Cech',
        'future_prediction': '🔮 Prognoza na Przyszłość',
        'correlations': '🔗 Macierz Korelacji',
        'target_distribution': '📊 Rozkład Wartości Docelowej'
    }
    
    for chart_key, chart_data in charts.items():
        if chart_data:
            # Dodaj tytuł wykresu
            title = chart_titles.get(chart_key, chart_key)
            story.append(Paragraph(title, subheading_style))
            
            try:
                # Konwertuj base64 na obraz
                image_data = base64.b64decode(chart_data)
                image_buffer = io.BytesIO(image_data)
                
                # Dodaj obraz do PDF
                img = Image(image_buffer, width=6*inch, height=4*inch)
                story.append(img)
                story.append(Spacer(1, 20))
                
            except Exception as e:
                # Jeśli nie można dodać obrazu, dodaj tekst
                story.append(Paragraph(f"<i>Wykres {title} - błąd ładowania</i>", normal_style))
                story.append(Spacer(1, 20))


def _convert_markdown_to_html(text):
    """Konwertuje podstawowe elementy markdown na HTML z obsługą polskich znaków"""
    
    # Pogrubienie
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # Kursywa
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    
    # Kod inline
    text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
    
    # Linki (podstawowe)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<link href="\2" color="blue">\1</link>', text)
    
    # Obsługa polskich znaków - upewnij się, że są poprawnie kodowane
    text = text.encode('utf-8').decode('utf-8')
    
    return text


def create_pdf_download_button(pdf_bytes, filename="raport_analizy.pdf"):
    """Tworzy przycisk do pobierania PDF"""
    
    import streamlit as st
    
    st.download_button(
        label="📄 Pobierz PDF",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf"
    )
