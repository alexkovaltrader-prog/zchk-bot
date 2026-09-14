"""Не создаёт заглушки. Новые картинки клади в assets/images с тем же именем, что в config.py."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "assets" / "images"


def main():
    IMAGES.mkdir(parents=True, exist_ok=True)
    print("Папка:", IMAGES)
    print("Положи сюда файлы с именами из config.py — они перекроют GitHub.")
    print("Сейчас бот берёт старые скрины с GitHub.")


if __name__ == "__main__":
    main()
