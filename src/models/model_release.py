"""Utilities to publish/download runtime model assets from GitHub Releases.

This keeps the git repository lightweight while still allowing a first-run
experience where runtime artifacts are downloaded automatically.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from src.config.settings import settings


def _release_base_url() -> str:
    if settings.model_release_base_url:
        return settings.model_release_base_url.rstrip("/")
    return f"https://github.com/{settings.github_repo}/releases/download/{settings.model_release_tag}"


def _asset_targets() -> dict[str, Path]:
    return {
        Path(settings.raw_runtime_bundle_path).name: Path(settings.raw_runtime_bundle_path),
        Path(settings.raw_runtime_manifest_path).name: Path(settings.raw_runtime_manifest_path),
        Path(settings.raw_runtime_threshold_path).name: Path(settings.raw_runtime_threshold_path),
        Path(settings.raw_runtime_coefficients_path).name: Path(settings.raw_runtime_coefficients_path),
    }


def missing_runtime_assets() -> dict[str, Path]:
    targets = _asset_targets()
    return {name: path for name, path in targets.items() if not path.exists()}


def download_runtime_assets(force: bool = False) -> list[Path]:
    """Download missing runtime assets from a GitHub Release.

    Args:
        force: When True, re-download files even if they exist.

    Returns:
        List of files downloaded.
    """
    targets = _asset_targets()
    base_url = _release_base_url()
    downloaded: list[Path] = []

    for asset_name, target_path in targets.items():
        if target_path.exists() and not force:
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"{base_url}/{asset_name}"

        try:
            with urlopen(url, timeout=settings.model_download_timeout_seconds) as response:
                data = response.read()
            target_path.write_bytes(data)
            downloaded.append(target_path)
        except HTTPError as exc:
            raise FileNotFoundError(
                f"Asset introuvable sur la release: {url} (HTTP {exc.code})"
            ) from exc
        except URLError as exc:
            raise ConnectionError(f"Impossible de telecharger l'asset: {url}") from exc

    return downloaded


def ensure_runtime_assets() -> list[Path]:
    """Ensure runtime assets are available locally, downloading if enabled."""
    missing = missing_runtime_assets()
    if not missing:
        return []

    if not settings.model_auto_download:
        missing_str = ", ".join(str(path) for path in missing.values())
        raise FileNotFoundError(
            "Artefacts runtime manquants et telechargement auto desactive: "
            f"{missing_str}"
        )

    return download_runtime_assets(force=False)


def _print_release_cli_guide() -> None:
    repo = settings.github_repo
    tag = settings.model_release_tag
    asset_paths = [str(path) for path in _asset_targets().values()]

    print("# Commandes CLI pour publier les artefacts runtime")
    print("gh auth status")
    print(
        f"gh release create {tag} --repo {repo} "
        f"--title \"{tag}\" --notes \"Runtime assets for UI/API bootstrap\""
    )
    for asset in asset_paths:
        print(f"gh release upload {tag} {asset} --repo {repo} --clobber")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage runtime assets from GitHub Releases.")
    parser.add_argument("--download", action="store_true", help="Download missing runtime assets")
    parser.add_argument("--force", action="store_true", help="Force re-download of runtime assets")
    parser.add_argument("--print-cli", action="store_true", help="Print gh release CLI commands")
    args = parser.parse_args()

    if args.print_cli:
        _print_release_cli_guide()

    if args.download:
        files = download_runtime_assets(force=args.force) if args.force else ensure_runtime_assets()
        if files:
            print("Telecharges:")
            for f in files:
                print(f"- {f}")
        else:
            print("Tous les artefacts runtime sont déjà présents.")


if __name__ == "__main__":
    main()
