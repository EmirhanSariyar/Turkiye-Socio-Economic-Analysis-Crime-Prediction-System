from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
EXTERNAL_DIR = BASE_DIR / "data" / "external"


def print_inventory() -> None:
    for category_dir in sorted(EXTERNAL_DIR.iterdir()):
        if not category_dir.is_dir():
            continue

        print(f"[{category_dir.name}]")
        for file_path in sorted(category_dir.iterdir()):
            if file_path.is_file():
                print(f" - {file_path.name}")
        print()


if __name__ == "__main__":
    print_inventory()
