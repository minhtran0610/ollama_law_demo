import sys
from pathlib import Path


def main() -> None:
    scripts_dir = Path(__file__).resolve().parent.parent.parent / "scripts"
    sys.path.insert(0, str(scripts_dir))
    import context_demo

    context_demo.main()
