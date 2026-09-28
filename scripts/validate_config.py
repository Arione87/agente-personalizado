"""Valida a configuração e os arquivos locais antes da publicação."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import load_settings  # noqa: E402


def main() -> None:
    settings = load_settings()
    logo = ROOT / settings.assistant.logo
    if not logo.is_file():
        raise ValueError(f"a logo não existe: {settings.assistant.logo}")
    print("Configuração válida.")


if __name__ == "__main__":
    main()
