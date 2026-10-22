"""
Télécharge les fichiers MetaCardis (MetaDrugs workflow) depuis Zenodo.

Source  : Forslund et al., MetaCardis Consortium — https://doi.org/10.5281/zenodo.6242715
Licence : Creative Commons Attribution 4.0 (CC BY 4.0)

Usage :
    python scripts/download_data.py           # télécharge ce qui manque
    python scripts/download_data.py --force   # retélécharge tout
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import tarfile
from pathlib import Path

import requests

# --- Chemins ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent      # racine du projet
RAW_DIR = ROOT / "data" / "raw"

# --- Source ----------------------------------------------------------------
ZENODO_RECORD = "6242715"                           # version 1.1.0
BASE_URL = f"https://zenodo.org/records/{ZENODO_RECORD}/files"

# nom du fichier -> empreinte md5 publiée par Zenodo
FILES: dict[str, str] = {
    "output_all_formatted_noc_uncollapsed_complete.tsv": "a712b9b11712912a9f52bf31515ccb63",
    "feature_names.tar.gz": "b7017c76f445ad5e87ea9d1fc6c6da50",
    "metadata.tar.gz": "ecde6ab712cc1a664740c2f3aa748e4c",
    "metaDrugs_workflow_readme.txt": "a012c0b6f2f602340721e0dc360ef325",
}

CHUNK = 1024 * 1024  # on lit/écrit par blocs de 1 Mo


def md5sum(path: Path) -> str:
    """Calcule l'empreinte md5 d'un fichier, bloc par bloc (peu de mémoire)."""
    h = hashlib.md5()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def download(name: str, expected_md5: str, force: bool = False) -> Path:
    """Télécharge un fichier s'il manque ou s'il est corrompu, puis vérifie son md5."""
    dest = RAW_DIR / name

    # 1. Cache : si le fichier est déjà là et intact, on ne retélécharge pas
    if dest.exists() and not force:
        if md5sum(dest) == expected_md5:
            print(f"[ok]   {name} déjà présent et valide")
            return dest
        print(f"[warn] {name} corrompu -> nouveau téléchargement")

    # 2. Téléchargement en streaming dans un fichier temporaire .part
    url = f"{BASE_URL}/{name}?download=1"
    tmp = dest.with_name(dest.name + ".part")
    print(f"[get]  {name}")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with tmp.open("wb") as f:
            for chunk in r.iter_content(CHUNK):
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r       {done / total:6.1%}  ({done / 1e6:.1f} / {total / 1e6:.1f} Mo)", end="")
    print()

    # 3. Validation : le md5 doit correspondre exactement à celui de Zenodo
    got = md5sum(tmp)
    if got != expected_md5:
        tmp.unlink()
        raise ValueError(f"md5 incorrect pour {name} : {got} au lieu de {expected_md5}")

    tmp.replace(dest)  # on ne renomme qu'une fois le fichier validé
    print(f"[ok]   {name} validé (md5)")
    return dest


def extract(archive: Path) -> None:
    """Décompresse une archive .tar.gz dans un dossier du même nom, de façon sécurisée."""
    target = RAW_DIR / archive.name.removesuffix(".tar.gz")
    if target.exists() and any(target.iterdir()):
        print(f"[ok]   {target.name}/ déjà extrait")
        return
    target.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive, "r:gz") as tar:
        if hasattr(tarfile, "data_filter"):
            # Python >= 3.12 : filtre officiel contre les chemins dangereux
            tar.extractall(target, filter="data")
        else:
            # Versions plus anciennes : on vérifie chaque fichier nous-mêmes
            root = target.resolve()
            for member in tar.getmembers():
                path = (target / member.name).resolve()
                if not path.is_relative_to(root) or member.issym() or member.islnk():
                    raise ValueError(f"Chemin suspect dans l'archive : {member.name}")
            tar.extractall(target)
    print(f"[ok]   {archive.name} extrait dans data/raw/{target.name}/")


def main() -> int:
    parser = argparse.ArgumentParser(description="Télécharge les données MetaCardis depuis Zenodo.")
    parser.add_argument("--force", action="store_true", help="retélécharger même si les fichiers existent")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    try:
        for name, md5 in FILES.items():
            path = download(name, md5, force=args.force)
            if name.endswith(".tar.gz"):
                extract(path)
    except (requests.RequestException, ValueError, tarfile.TarError) as err:
        print(f"[erreur] {err}", file=sys.stderr)
        return 1

    print("\nTerminé. Fichiers disponibles dans data/raw/")
    return 0


if __name__ == "__main__":
    sys.exit(main())