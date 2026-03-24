from __future__ import annotations

import argparse
from pathlib import Path
import zipfile


def unzip_file(zip_path: Path, destination: Path | None = None) -> Path:
    if not zip_path.exists():
        raise FileNotFoundError(f"Archive introuvable: {zip_path}")

    if zip_path.suffix.lower() != ".zip":
        raise ValueError(f"Le fichier n'est pas une archive ZIP: {zip_path}")

    output_dir = destination or zip_path.with_suffix("")
    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(output_dir)

    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Dezipper une archive ZIP")
    parser.add_argument("zip_file", type=Path, help="Chemin du fichier ZIP")
    parser.add_argument(
        "-d",
        "--destination",
        type=Path,
        help="Dossier de destination pour l'extraction",
    )
    args = parser.parse_args()

    extracted_to = unzip_file(args.zip_file, args.destination)
    print(f"Archive extraite dans: {extracted_to}")


if __name__ == "__main__":
    main()