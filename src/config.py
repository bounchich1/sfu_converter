from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH


class SIBFUConfig:
    """Конфигурация стандартов оформления СФУ"""
    
    FONT_NAME = 'Times New Roman'
    FONT_SIZE = Pt(14)
    FONT_COLOR_RGB = (0, 0, 0)
    LINE_SPACING_NORMAL = 1.5
    ALIGNMENT = WD_ALIGN_PARAGRAPH.JUSTIFY
    FIRST_LINE_INDENT = Cm(1.25)
    
    H1 = {
        'align': WD_ALIGN_PARAGRAPH.CENTER,
        'bold': True,
        'line_spacing': 1.0,
        'indent': Cm(0),
        'space_before': Pt(0),
        'space_after': Pt(0)
    }

    H2 = {
        'align': WD_ALIGN_PARAGRAPH.LEFT,
        'bold': True,
        'line_spacing': 1.0,
        'indent': Cm(0),
        'space_before': Pt(0),
        'space_after': Pt(0)
    }

    H3 = {
        'align': WD_ALIGN_PARAGRAPH.LEFT,
        'bold': False,
        'line_spacing': 1.0,
        'indent': Cm(0),
        'space_before': Pt(0),
        'space_after': Pt(0)
    }

    CAPTION_IMAGE = {
        'align': WD_ALIGN_PARAGRAPH.CENTER,
        'indent': Cm(0),
        'bold': False,
        'line_spacing': 1.5,
        'space_before': Pt(0),
        'space_after': Pt(0)
    }

    CAPTION_TABLE = {
        'align': WD_ALIGN_PARAGRAPH.LEFT,
        'indent': Cm(0),
        'bold': False,
        'line_spacing': 1.5,
        'space_before': Pt(0),
        'space_after': Pt(0)
    }

    EMPTY_BEFORE_HEADER = {
        'line_spacing': 0.5,
        'space_before': Pt(0),
        'space_after': Pt(0)
    }

    EMPTY_AFTER_HEADER = {
        'line_spacing': 1,
        'space_before': Pt(0),
        'space_after': Pt(0)
    }

    EMPTY_AFTER_IMAGE = {
        'line_spacing': 0.5,
        'space_before': Pt(0),
        'space_after': Pt(0)
    }

    EMPTY_BEFORE_IMAGE = {
        'line_spacing': 0.8,
        'space_before': Pt(0),
        'space_after': Pt(0)
    }

    EMPTY_BEFORE_TABLE = {
        'line_spacing': 0.5,
        'space_before': Pt(0),
        'space_after': Pt(0)
    }

    EMPTY_AFTER_TABLE = {
        'line_spacing': 1,
        'space_before': Pt(0),
        'space_after': Pt(0)
    }

    MARGINS = {
        'top': Cm(2),
        'bottom': Cm(2),
        'left': Cm(3),
        'right': Cm(1.5)
    }
        
    # === Изображения ===
    IMAGE = {
        'line_spacing': 1.5,
        'alignment': WD_ALIGN_PARAGRAPH.CENTER,
        'width': None,           # Или Cm(10) для фиксированной ширины
        'height': None,          # Или None для авто-расчета
        'dpi': (96, 96),
        'format': 'PNG',         # Или 'JPEG'
        'max_width': Cm(1.5),     # Максимальная ширина
    }
    
    TABLE_CELL_PADDING = Pt(6)