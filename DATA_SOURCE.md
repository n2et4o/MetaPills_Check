# Jeu de données / Dataset

**Data analysis pipeline for investigating drug-host-microbiome relationships in cardiometabolic disease (MetaCardis cohort)** — version 1.1.0

- **Auteurs / Authors :** Forslund S.K., Chakaroun R., Zimmermann-Kogadeeva M., Markó L., Aron-Wisnewsky J., Nielsen T., Birkner T. (MetaCardis Consortium)
- **DOI :** [10.5281/zenodo.6242715](https://doi.org/10.5281/zenodo.6242715)
- **Lien direct / Direct link :** https://zenodo.org/records/6242715
- **Portail / Portal :** data.europa.eu — fiche du jeu / dataset page : https://data.europa.eu/data/combined?locale=en&query=drug-host-microbiome&page=1
- **Licence :** [Creative Commons Attribution 4.0 (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Article associé / Related paper :** Forslund et al. (2021). *Combinatorial, additive and dose-dependent drug–microbiome associations.* Nature 600, 500–505.

## Fichiers utilisés / Files used

| Fichier / File | Taille / Size | md5 | Usage |
|---|---|---|---|
| `output_all_formatted_noc_uncollapsed_complete.tsv` | 82,1 Mo | `a712b9b11712912a9f52bf31515ccb63` | Toutes les associations maladie / médicaments → microbiome & métabolome |
| `feature_names.tar.gz` | 447 ko | `b7017c76f445ad5e87ea9d1fc6c6da50` | Noms lisibles des médicaments et variables |
| `metadata.tar.gz` | 185 ko | `ecde6ab712cc1a664740c2f3aa748e4c` | Cohorte (affichée **uniquement agrégée**) |
| `metaDrugs_workflow_readme.txt` | 7,7 ko | `a012c0b6f2f602340721e0dc360ef325` | Documentation des auteurs |

Les fichiers bruts ne sont **pas** inclus (taille) : `python scripts/download_data.py` les télécharge et vérifie leur md5.
Les fichiers légers dérivés sont dans `data/processed/`.

Raw files are **not** included (size): `python scripts/download_data.py` downloads them and checks their md5.
Light derived files are in `data/processed/`.
