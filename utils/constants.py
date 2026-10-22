"""Constantes partagées par tout le projet (chemins, seuils, libellés)."""
from pathlib import Path

# --- Chemins -----------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

RESULTS_FILE = RAW_DIR / "output_all_formatted_noc_uncollapsed_complete.tsv"

ASSOCIATIONS_PARQUET = PROCESSED_DIR / "associations.parquet"
COHORT_PARQUET = PROCESSED_DIR / "cohort.parquet"
DRUG_USAGE_PARQUET = PROCESSED_DIR / "drug_usage.parquet"
QUALITY_JSON = PROCESSED_DIR / "quality_report.json"

# --- Seuils (documentés dans le README) -----------------------------------------
FDR_DEFAULT = 0.05        # seuil de significativité par défaut (taux de fausses découvertes)
MIN_CELL_SIZE = 10        # confidentialité : aucun groupe de moins de 10 patients n'est affiché
POLYPHARMACY_MIN = 5      # définition usuelle : >= 5 médicaments différents

# --- Groupes de patients MetaCardis (codes PATGROUPFINAL_C) ---------------------
GROUP_LABELS = {
    "1":  {"en": "Metabolic syndrome",            "fr": "Syndrome métabolique"},
    "2a": {"en": "Obesity",                       "fr": "Obésité"},
    "2b": {"en": "Obesity + bariatric surgery",   "fr": "Obésité + chirurgie bariatrique"},
    "3":  {"en": "Type 2 diabetes",               "fr": "Diabète de type 2"},
    "4":  {"en": "Acute coronary disease",        "fr": "Coronaropathie aiguë"},
    "5":  {"en": "Chronic coronary disease",      "fr": "Coronaropathie chronique"},
    "6":  {"en": "Coronary disease + heart failure", "fr": "Coronaropathie + insuffisance cardiaque"},
    "7":  {"en": "Heart failure (no coronary disease)", "fr": "Insuffisance cardiaque (sans coronaropathie)"},
    "8":  {"en": "Healthy controls",              "fr": "Témoins sains"},
}

# --- Premier niveau de la classification ATC (groupe anatomique) -----------------
ATC_LEVEL1 = {
    "A": {"en": "Alimentary tract & metabolism", "fr": "Voies digestives & métabolisme"},
    "B": {"en": "Blood",                         "fr": "Sang"},
    "C": {"en": "Cardiovascular system",         "fr": "Système cardiovasculaire"},
    "D": {"en": "Dermatologicals",               "fr": "Dermatologie"},
    "G": {"en": "Genito-urinary & sex hormones", "fr": "Génito-urinaire & hormones sexuelles"},
    "H": {"en": "Systemic hormones",             "fr": "Hormones systémiques"},
    "J": {"en": "Anti-infectives",               "fr": "Anti-infectieux"},
    "L": {"en": "Antineoplastics & immunomodulators", "fr": "Antinéoplasiques & immunomodulateurs"},
    "M": {"en": "Musculo-skeletal system",       "fr": "Système musculo-squelettique"},
    "N": {"en": "Nervous system",                "fr": "Système nerveux"},
    "P": {"en": "Antiparasitics",                "fr": "Antiparasitaires"},
    "R": {"en": "Respiratory system",            "fr": "Système respiratoire"},
    "S": {"en": "Sensory organs",                "fr": "Organes sensoriels"},
    "V": {"en": "Various",                       "fr": "Divers"},
}

# --- Libellés des catégories de robustesse (créées dans utils/prep.py) -----------
ROBUSTNESS_LABELS = {
    "robust":          {"en": "Robust (strictly deconfounded)", "fr": "Robuste (strictement déconfondue)"},
    "no_covariate":    {"en": "Robust (no competing factor)",   "fr": "Robuste (aucun facteur concurrent)"},
    "lax":             {"en": "Laxly deconfounded",             "fr": "Déconfondue (critère souple)"},
    "ambiguous":       {"en": "Ambiguous",                      "fr": "Ambiguë"},
    "confounded":      {"en": "Confounded",                     "fr": "Confondue"},
    "not_significant": {"en": "Not significant",                "fr": "Non significative"},
}

# --- Libellés des types d'effecteurs -------------------------------------------
EFFECTOR_KIND_LABELS = {
    "drug":    {"en": "Drugs",                       "fr": "Médicaments"},
    "disease": {"en": "Disease status",              "fr": "Statut de maladie"},
    "other":   {"en": "Other factors (lifestyle, clinical)", "fr": "Autres facteurs (mode de vie, clinique)"},
}

# --- Libellés des types de variables mesurées ----------------------------------
CLASS_LABELS = {
    "Metabolome":          {"en": "Metabolome (blood, urine)", "fr": "Métabolome (sang, urine)"},
    "Microbiome taxonomy": {"en": "Gut bacteria (species)",    "fr": "Bactéries intestinales (espèces)"},
    "Microbiome function": {"en": "Bacterial functions",       "fr": "Fonctions bactériennes"},
}

# --- Pays de recrutement (valeurs de CENTER_C) ----------------------------------
COUNTRY_LABELS = {
    "France":   {"en": "France",  "fr": "France"},
    "Germany":  {"en": "Germany", "fr": "Allemagne"},
    "Danemark": {"en": "Denmark", "fr": "Danemark"},
}

# --- Traductions françaises des variables les plus fréquentes -------------------
# (les noms anglais viennent du fichier officiel feature_names/metadata_names)
VARIABLE_FR = {
    "CENTER_C": "Pays de recrutement", "AGE": "Âge", "BMI_C": "IMC",
    "GENDER": "Sexe", "Status": "Statut de maladie", "DRUGTOTAL": "Nombre total de médicaments",
    "ANTIDIAB_C": "Antidiabétiques", "METFORMIN_C": "Metformine", "STATINE_C": "Statines",
    "ANTILIPID_C": "Hypolipémiants", "ANTIHTA_C": "Antihypertenseurs", "ASA_C": "Aspirine",
    "DPPIV_C": "Inhibiteurs de la DPP-4", "PPI_AND_PPI_RELATED_C": "Inhibiteurs de la pompe à protons",
    "INSULIN_C": "Insuline", "SU_C": "Sulfamides hypoglycémiants", "BETA_BL_C": "Bêtabloquants",
    "ANTIBIOTICS_TOTAL": "Cures d'antibiotiques", "SMOKE": "Tabac",
    "aHEI": "Qualité de l'alimentation (aHEI)", "DASH": "Score alimentaire DASH",
}
