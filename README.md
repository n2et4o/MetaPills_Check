# 🧬 Médicaments, microbiote et métabolisme · Drugs, microbiome and metabolism

**Un récit de données interactif (Streamlit) sur la cohorte européenne MetaCardis - en français et en anglais.**
**An interactive Streamlit data story on the European MetaCardis cohort - in French and English.**

- 🌐 **Application en ligne / Live app :**  [`Metapills_check`](https://biubqvxn92kk2cuqmgvk43.streamlit.app/?lang=fr)
- 🎬 **Vidéo de démonstration / Demo video :** `À COMPLÉTER / TO FILL IN`
- 👤 **Auteur / Author :** Joss DOUNIAMA OKANA - 20220848 - groupe BIO
- 📦 **Données / Data :** MetaCardis, Zenodo, DOI [10.5281/zenodo.6242715](https://doi.org/10.5281/zenodo.6242715), licence CC BY 4.0 - détails dans [`DATA_SOURCE.md`](DATA_SOURCE.md)

*English version below → [English](#english)*

---

## 🇫🇷 Français

### 1. La question

Les patients atteints de maladies cardiométaboliques (obésité, diabète de type 2, maladies coronariennes) prennent souvent **plusieurs médicaments à la fois**. Ces traitements modifient aussi les **bactéries intestinales** et les **molécules du sang et de l'urine**.

> **Les médicaments laissent-ils une empreinte plus forte que la maladie elle-même ? Et quels liens observés sont trompeurs ?**

**Public visé :** étudiants et chercheurs (biologie, pharmacologie, nutrition), cliniciens curieux des effets « hors cible », et grand public grâce à une page vulgarisée.

**Questions du récit :**
1. Les médicaments pèsent-ils plus que la maladie ?
2. Quels médicaments touchent quelles bactéries et quels métabolites ?
3. Quelle part des liens observés est trompeuse, et pourquoi ?
4. *(grand public)* Pour **un** médicament : son effet est-il plus fort que celui de la maladie, et vient-il vraiment de lui ou du milieu ?

### 2. L'arc narratif (7 sections)

| # | Section | Rôle dans le récit |
|---|---|---|
| 1 | Pourquoi c'est important | **Accroche** + contexte, glossaire vulgarisé, cohorte (carte, polymédication) |
| 2 | Vue d'ensemble | Médicaments vs maladie vs mode de vie - comparaison **en taux** |
| 3 | Le réseau d'interactions | Réseau médicaments → microbiote / métabolome, « carrefours » partagés |
| 4 | Analyses détaillées | Un médicament à la loupe, heatmap, **facteurs de confusion** |
| 5 | Et mon médicament ? | Page **grand public** : plus fort que la maladie ? médicament ou milieu ? |
| 6 | Qualité des données | Nettoyage, contrôles, valeurs manquantes, hypothèses |
| 7 | Conclusions & limites | 3 messages clés, **implications**, limites, pistes |

Modèles narratifs utilisés : **réseau / flux**, **classements**, **comparaison de groupes** (carte + petits multiples) et **exploration interactive** (« et si… ? »).

### 3. Lancer l'application en local

Prérequis : Python 3.11 ou plus récent.

```bash
# 1. Environnement
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows (PowerShell)
source .venv/bin/activate           # macOS / Linux
pip install -r requirements.txt

# 2. Lancer (les données pré-traitées sont déjà dans data/processed/)
streamlit run app.py
```

**Reconstruire les données depuis la source (optionnel, ~83 Mo) :**

```bash
python scripts/download_data.py      # télécharge depuis Zenodo + vérifie le md5 (avec cache)
python scripts/build_processed.py    # nettoie et produit data/processed/
python scripts/check_locales.py      # vérifie que le français et l'anglais sont complets
```

### 4. Structure du projet

```
app.py                     point d'entrée : langue, navigation, filtres, sections
requirements.txt           dépendances (versions figées)
DATA_SOURCE.md             source, licence, fichiers, empreintes md5
.streamlit/config.toml     thème (contrastes accessibles)
locales/fr.json, en.json   tous les textes de l'app (aucun texte en dur dans le code)
scripts/
  download_data.py         téléchargement + vérification md5 + extraction sécurisée
  build_processed.py       nettoyage -> fichiers légers + rapport qualité
  check_locales.py         contrôle des traductions
  make_submission.py       crée le zip de rendu
utils/
  constants.py             chemins, seuils, libellés
  prep.py                  nettoyage, validation, feature engineering (sans Streamlit)
  io.py                    chargement avec cache (invalidé si les données changent)
  filters.py               filtres globaux (mis en cache)
  analysis.py              analyses « Et mon médicament ? » (sans Streamlit)
  network.py               construction du réseau, centralités, disposition
  viz.py                   graphiques Plotly au style uniforme
  i18n.py                  traduction FR / EN, formats de nombres
sections/                  une section du récit par fichier
data/processed/            données légères utilisées par l'app (versionnées)
data/raw/                  données brutes (non versionnées)
```

### 5. Travail sur les données

**Nettoyage** (`utils/prep.py`, chiffres réels) :

| Étape | Lignes |
|---|---|
| Fichier brut | 273 322 |
| − doublons exacts | − 42 847 |
| − tailles d'effet infinies | − 11 970 |
| − doublons sur la clé (test, facteur, groupe, variable) | − 3 895 |
| **Données propres** | **214 610** |

**Contrôles automatiques :** empreinte md5 de chaque fichier, présence des colonnes requises, FDR dans [0, 1], taille d'effet finie, identifiants patients uniques (2 173), jointure démographie × médicaments vérifiée « un pour un ».

**Feature engineering :** type de facteur (médicament / maladie / autre), statut de robustesse lisible (robuste, souple, confondu), liste des variables qui confondent chaque association, groupe de patients, classe ATC, direction et intensité de l'effet, −log10(FDR), noms lisibles des variables.

**Valeurs manquantes :** âge et IMC manquent pour **100 % des 527 patients danois** (données retirées par les auteurs pour respecter la loi danoise) → manquants **non aléatoires**, signalés dans l'app. Les colonnes « Comparison… » (vides à 63–97 %) sont retirées.

**Hypothèses documentées :**
- doublons sur la clé : on garde le résultat le plus significatif ;
- statut « OK » classé robuste ; statut donné sous forme de liste de variables = association confondue par ces variables ;
- polymédication = au moins 5 médicaments différents ;
- réseau : seuls les tests « prise d'un médicament », pour éviter les doublons avec doses et combinaisons ;
- « Et mon médicament ? » : empreinte = part des variables testées modifiées de façon robuste ; « plus fort / plus faible » = écart de plus de 20 % entre les taux.

### 6. Choix de visualisation et d'interface

- Une couleur = une entité, partout (médicament = bleu, maladie = orange, autres = vert d'eau).
- Palette **vérifiée pour le daltonisme** ; la **forme** des symboles double la couleur dans le réseau.
- Échelle divergente bleu (baisse) / rouge (hausse) ; échelles de quantité à une seule teinte.
- Chaque graphique a un titre-message, un sous-titre, une infobulle et une **vue tableau** téléchargeable (CSV).
- Encadrés 💡 « à retenir » **calculés à partir des données** (ils changent avec les filtres).
- Bouton de langue FR / EN, conservé dans l'URL (`?lang=en`) ; nombres au format de la langue.

### 7. Ingénierie et performance

- Nettoyage lourd fait **une seule fois** (`build_processed.py`) → l'app ne lit que des fichiers parquet légers.
- `st.cache_data` sur le chargement et le filtrage ; le cache est **invalidé automatiquement** quand les données changent.
- Code séparé en couches : données (`prep`, `io`), analyses (`analysis`, `network`), affichage (`viz`, `sections`).
- Dépendances figées ; l'app démarre depuis un clone propre, sans téléchargement.

### 8. Limites et éthique

- **Corrélation ≠ causalité** : associations statistiques d'une étude observationnelle.
- **Données secondaires** : nous visualisons les résultats publiés par les auteurs, sans refaire leurs tests.
- Patients danois : âge et IMC non publiés. Une grande partie du métabolome n'est pas annotée chimiquement. Pas de suivi dans le temps.
- **Confidentialité** : aucune donnée individuelle n'est publiée ; seuls des agrégats, sans groupe de moins de 10 patients.
- **Pas un avis médical** : l'app décrit des tendances de groupe, pas l'effet d'un médicament chez une personne.

### 9. Déploiement (Streamlit Community Cloud)

1. Pousser le dossier sur un dépôt GitHub **public** (avec `data/processed/`, sans `data/raw/`).
2. Sur [share.streamlit.io](https://share.streamlit.io) : *Create app* → dépôt, branche `main`, fichier `app.py`.
3. *Advanced settings* → **Python 3.13** → *Deploy*.

---

<a id="english"></a>
## 🇬🇧 English

### 1. The question

Patients with cardiometabolic diseases (obesity, type 2 diabetes, coronary disease) often take **several drugs at once**. These treatments also change **gut bacteria** and **molecules in blood and urine**.

> **Do drugs leave a stronger footprint than the disease itself? And which observed links are misleading?**

**Audience:** students and researchers (biology, pharmacology, nutrition), clinicians interested in off-target effects, and the general public through a plain-language page.

**Story questions:**
1. Do drugs weigh more than the disease?
2. Which drugs affect which bacteria and metabolites?
3. How many observed links are misleading, and why?
4. *(general public)* For **one** drug: is its effect stronger than the disease's, and does it really come from the drug or from the setting?

### 2. Story arc (7 sections)

| # | Section | Role |
|---|---|---|
| 1 | Why it matters | **Hook** + context, plain-language glossary, cohort (map, polypharmacy) |
| 2 | Overview | Drugs vs disease vs lifestyle - compared **as rates** |
| 3 | Interaction network | Drug → microbiome / metabolome network, shared "crossroads" |
| 4 | Deep dives | One drug up close, heatmap, **confounders** |
| 5 | What about my drug? | **General-public** page: stronger than the disease? drug or setting? |
| 6 | Data quality | Cleaning, checks, missing values, assumptions |
| 7 | Conclusions & limits | 3 key messages, **implications**, limits, next steps |

Narrative patterns: **network / flow**, **rankings**, **group comparison** (map + small multiples) and **interactive what-if exploration**.

### 3. Run locally

Requires Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows (PowerShell)
source .venv/bin/activate           # macOS / Linux
pip install -r requirements.txt
streamlit run app.py                # processed data is already in data/processed/
```

Rebuild data from source (optional, ~83 MB):

```bash
python scripts/download_data.py      # downloads from Zenodo + md5 check (cached)
python scripts/build_processed.py    # cleans and writes data/processed/
python scripts/check_locales.py      # checks French and English are complete
```

### 4. Data work

**Cleaning:** 273,322 raw rows → − 42,847 exact duplicates → − 11,970 infinite effect sizes → − 3,895 key duplicates → **214,610 clean rows**.

**Automated checks:** md5 checksum of every file, required columns, FDR in [0, 1], finite effect size, unique patient IDs (2,173), one-to-one demographics × drugs join.

**Feature engineering:** factor type (drug / disease / other), readable robustness status, list of confounding variables per association, patient group, ATC class, effect direction and strength, −log10(FDR), readable variable names.

**Missing values:** age and BMI are missing for **100% of the 527 Danish patients** (removed by the authors under Danish law) → **not missing at random**, flagged in the app.

**Documented assumptions:** key duplicates keep the most significant result; "OK" status = robust; a status given as a list of variables = confounded by them; polypharmacy = ≥ 5 different drugs; network uses "drug intake" tests only; "my drug" footprint = share of tested features robustly changed, with a 20% gap rule for stronger / weaker.

### 5. Visualisation, engineering, ethics

- One colour per entity everywhere; **colour-blind-checked** palette; symbol shapes double colour in the network; diverging blue/red for effect direction.
- Every chart has a message title, tooltip and downloadable **table view**; 💡 insights are **computed from the data**.
- FR / EN switch kept in the URL; locale-aware number formats.
- Heavy cleaning done once; `st.cache_data` with **automatic invalidation**; layered code (data / analysis / display); pinned dependencies.
- **Correlation ≠ causation**; secondary data; no individual data published (aggregates only, no group under 10 patients); **not medical advice**.

### 6. Deploy (Streamlit Community Cloud)

1. Push to a **public** GitHub repo (with `data/processed/`, without `data/raw/`).
2. On [share.streamlit.io](https://share.streamlit.io): *Create app* → repo, branch `main`, file `app.py`.
3. *Advanced settings* → **Python 3.13** → *Deploy*.

---

*Données : Forslund et al., MetaCardis Consortium - CC BY 4.0. Data: Forslund et al., MetaCardis Consortium - CC BY 4.0.*
