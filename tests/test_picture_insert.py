from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path
from PIL import Image
import io

# === 1. Создаём тестовую картинку ===
print("Создание тестовой картинки...")
img = Image.new('RGB', (400, 200), color='blue')
from PIL import ImageDraw
draw = ImageDraw.Draw(img)
draw.text((50, 90), "TEST IMAGE", fill='white')

img_path = Path(__file__).parent / 'test_image.png'
img.save(img_path, format='PNG', dpi=(96, 96))
print(f"✓ Картинка сохранена: {img_path}")

# === 2. Тест разных способов вставки ===
print("\n" + "="*60)
print("ТЕСТ СПОСОБОВ ВСТАВКИ КАРТИНКИ")
print("="*60)

doc = Document()

# --- Способ 1: run.add_picture() ---
print("\n[Способ 1] run.add_picture()")
para1 = doc.add_paragraph("Абзац с картинкой через run.add_picture()")
pf1 = para1.paragraph_format
pf1.line_spacing = 1.5
pf1.alignment = WD_ALIGN_PARAGRAPH.CENTER

run1 = para1.add_run()
print(f"  run методы с 'picture': {[m for m in dir(run1) if 'picture' in m.lower()]}")

if hasattr(run1, 'add_picture'):
    try:
        run1.add_picture(str(img_path), width=Cm(10))
        print("  ✅ run.add_picture() РАБОТАЕТ!")
    except Exception as e:
        print(f"  ❌ run.add_picture() ОШИБКА: {e}")
else:
    print("  ❌ run.add_picture() НЕ СУЩЕСТВУЕТ")

# --- Способ 2: doc.add_picture() ---
print("\n[Способ 2] doc.add_picture()")
doc.add_paragraph("Текст перед картинкой")

shape = doc.add_picture(str(img_path), width=Cm(10))
print(f"  shape тип: {type(shape).__name__}")
print(f"  shape атрибуты: {[a for a in dir(shape) if not a.startswith('_')][:15]}")

# Проверяем доступ к абзацу
print(f"  hasattr(shape, '_parent'): {hasattr(shape, '_parent')}")
print(f"  hasattr(shape, 'parent'): {hasattr(shape, 'parent')}")
print(f"  hasattr(shape, '_inline'): {hasattr(shape, '_inline')}")

if hasattr(shape, '_inline'):
    print(f"  hasattr(shape._inline, 'getparent'): {hasattr(shape._inline, 'getparent')}")

# Настраиваем последний абзац (где картинка)
para_img = doc.paragraphs[-1]
para_img.paragraph_format.line_spacing = 1.5
para_img.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
print("  ✅ Настроен paragraphs[-1]")

# --- Способ 3: run.add_image() (альтернатива) ---
print("\n[Способ 3] run.add_image()")
para3 = doc.add_paragraph("Абзац с run.add_image()")
run3 = para3.add_run()
print(f"  run методы с 'image': {[m for m in dir(run3) if 'image' in m.lower()]}")

if hasattr(run3, 'add_image'):
    try:
        run3.add_image(str(img_path))
        print("  ✅ run.add_image() РАБОТАЕТ!")
    except Exception as e:
        print(f"  ❌ run.add_image() ОШИБКА: {e}")
else:
    print("  ❌ run.add_image() НЕ СУЩЕСТВУЕТ")

# === 3. Сохранение ===
output_path = Path(__file__).parent / 'test_picture_methods.docx'
doc.save(str(output_path))
print(f"\n✓ Документ сохранён: {output_path}")
print("="*60)

# === 4. Итоговая таблица ===
print("\nИТОГИ:")
print("-"*60)
print("| Метод              | Существует | Работает |")
print("-"*60)
print(f"| run.add_picture()  | {hasattr(run1, 'add_picture')} | {'✅' if hasattr(run1, 'add_picture') else '❌'} |")
print(f"| run.add_image()    | {hasattr(run3, 'add_image')} | {'✅' if hasattr(run3, 'add_image') else '❌'} |")
print(f"| doc.add_picture()  | True | ✅ |")
print(f"| shape._parent      | {hasattr(shape, '_parent')} | {'✅' if hasattr(shape, '_parent') else '❌'} |")
print(f"| shape.parent       | {hasattr(shape, 'parent')} | {'✅' if hasattr(shape, 'parent') else '❌'} |")
print("-"*60)
print("\nОткройте test_picture_methods.docx и проверьте визуально!")