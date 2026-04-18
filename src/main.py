import logging
from pathlib import Path
from converter import TextToDocxConverter
from validator import StyleValidator
from menu import ConsoleMenu


def setup_logging(log_dir):
    """Настраивает логирование в файл и консоль"""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'converter.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ],
        force=True
    )
    return logging.getLogger(__name__)


def main():
    """Точка входа в приложение"""
    base_dir = Path(__file__).resolve().parent.parent
    
    logger = setup_logging(base_dir / 'logs')
    logger.info("Запуск приложения")
    
    converter = TextToDocxConverter(base_dir=base_dir)
    validator = StyleValidator()
    menu = ConsoleMenu(base_dir)
    
    try:
        menu.run(converter, validator)
    except KeyboardInterrupt:
        logger.info("Приложение завершено пользователем")
        print("\n\nПриложение завершено")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print(f"\n✗ Ошибка: {e}")


if __name__ == "__main__":
    main()