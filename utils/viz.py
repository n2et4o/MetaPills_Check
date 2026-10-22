"""
Fonctions de graphiques (Plotly) au style uniforme.

Règles appliquées partout :
- une couleur = une entité, toujours la même (un médicament reste bleu partout) ;
- palette vérifiée pour le daltonisme (validateur OKLab, voir README) ;
- traits fins, grille discrète, pas de double axe ;
- le texte reste en encre neutre, jamais dans la couleur des données ;
- chaque graphique a une légende, une infobulle et un tableau équivalent dans l'app.
"""
from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# =============================================================================
# Palette (validée : contraste, séparation daltonisme, lisibilité)
# =============================================================================
INK = "#1A1A1A"         # texte principal
INK_2 = "#52514E"       # texte secondaire
MUTED = "#898781"       # axes, annotations discrètes
GRID = "#E1E0D9"        # grille (trait fin, plein)
SURFACE = "#FFFFFF"     # fond des graphiques
NEUTRAL = "#F0EFEC"     # milieu de l'échelle divergente

# Type de facteur : médicament / maladie / autres
KIND_COLORS = {"drug": "#2A78D6", "disease": "#EB6834", "other": "#1BAF7A"}

# Type de variable mesurée (+ forme de marqueur = 2e indice, pas seulement la couleur)
CLASS_COLORS = {
    "Metabolome": "#D55181",
    "Microbiome taxonomy": "#008300",
    "Microbiome function": "#C98500",
}
CLASS_SYMBOLS = {"Metabolome": "circle", "Microbiome taxonomy": "square",
                 "Microbiome function": "triangle-up"}

# Direction de l'effet : bleu = baisse, rouge = hausse (échelle divergente)
DECREASE, INCREASE = "#2A78D6", "#E34948"
DIVERGING = [[0.0, DECREASE], [0.5, NEUTRAL], [1.0, INCREASE]]

# Magnitude : une seule teinte, du clair au foncé
SEQUENTIAL = ["#CDE2FB", "#9EC5F4", "#6DA7EC", "#3987E5", "#256ABF", "#184F95", "#0D366B"]

FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"


def base_layout(fig: go.Figure, title: str = "", subtitle: str = "",
                height: int = 420) -> go.Figure:
    """Style commun : titre + sous-titre, fond blanc, grille fine, police système."""
    full_title = f"<b>{title}</b>" + (f"<br><span style='font-size:13px;color:{INK_2}'>{subtitle}</span>"
                                      if subtitle else "")
    from utils.i18n import get_lang
    fig.update_layout(
        separators=", " if get_lang() == "fr" else ".,",     # 3,2 et 1 284 en français
        title=dict(text=full_title, x=0, xanchor="left", font=dict(size=17, color=INK)),
        font=dict(family=FONT, size=13, color=INK),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        height=height,
        margin=dict(l=10, r=30, t=85 if subtitle else 55, b=60),
        hoverlabel=dict(bgcolor=SURFACE, font=dict(family=FONT, color=INK), bordercolor=GRID),
        # Légende sous le graphique : ne chevauche jamais le titre
        legend=dict(orientation="h", yanchor="top", y=-0.12, x=0, title_text="",
                    font=dict(color=INK_2), traceorder="normal"),
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=GRID, zerolinecolor=MUTED, zerolinewidth=1,
                     tickfont=dict(color=MUTED), title_font=dict(color=INK_2))
    fig.update_yaxes(gridcolor=GRID, linecolor=GRID, zerolinecolor=MUTED, zerolinewidth=1,
                     tickfont=dict(color=MUTED), title_font=dict(color=INK_2))
    return fig


# =============================================================================
# 1. Classement horizontal (top N)
# =============================================================================
def ranked_bars(df: pd.DataFrame, label_col: str, value_col: str, color: str,
                title: str, subtitle: str = "", value_name: str = "",
                highlight: set | None = None, color_col: str | None = None,
                sort: bool = True, value_format: str = ",.0f") -> go.Figure:
    """
    Barres horizontales, valeur écrite au bout de chaque barre.
    `highlight` : libellés à mettre en couleur ; les autres passent en gris (emphase).
    `color_col` : colonne contenant une couleur par barre (ex. selon le type de facteur).
    `sort=False` : garde l'ordre du tableau (utile pour des étapes successives).
    """
    d = df.sort_values(value_col) if sort else df.iloc[::-1]      # 1re ligne en haut
    if color_col:
        colors = list(d[color_col])
    else:
        colors = [color if (highlight is None or lab in highlight) else "#C3C2B7"
                  for lab in d[label_col]]
    fig = go.Figure(go.Bar(
        x=d[value_col], y=d[label_col], orientation="h",
        marker=dict(color=colors, cornerradius=4),
        texttemplate="%{x:" + value_format + "}",          # séparateurs selon la langue
        textposition="outside", textfont=dict(color=INK_2), cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>" + value_name + " : %{x:" + value_format + "}<extra></extra>",
    ))
    fig.update_layout(bargap=0.35, uniformtext=dict(minsize=11, mode="show"))
    # 15 % d'espace à droite pour que la valeur écrite au bout de la barre ne soit pas coupée
    fig.update_xaxes(showgrid=False, showticklabels=False, title_text="",
                     range=[0, float(d[value_col].max()) * 1.15 if len(d) else 1])
    fig.update_yaxes(title_text="", tickfont=dict(color=INK_2))
    return base_layout(fig, title, subtitle, height=max(300, 34 * len(d) + 110))


# =============================================================================
# 1 bis. Barres divergentes (hausse à droite, baisse à gauche)
# =============================================================================
def diverging_bars(df: pd.DataFrame, label_col: str, value_col: str, title: str,
                   subtitle: str = "", labels: dict | None = None) -> go.Figure:
    """Effets signés autour de 0 : rouge = hausse, bleu = baisse. Une seule échelle."""
    labels = labels or {}
    d = df.sort_values(value_col)
    fig = go.Figure(go.Bar(
        x=d[value_col], y=d[label_col], orientation="h",
        marker=dict(color=[INCREASE if v >= 0 else DECREASE for v in d[value_col]],
                    cornerradius=4),
        texttemplate="%{x:+.2f}", textposition="outside",
        textfont=dict(color=INK_2), cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>" + labels.get("effect", "Effect")
                      + " : %{x:+.3f}<extra></extra>",
    ))
    lim = max(0.1, float(d[value_col].abs().max()) * 1.25) if len(d) else 1
    fig.update_layout(bargap=0.35)
    fig.update_xaxes(range=[-lim, lim], title_text=labels.get("x", ""), zeroline=True)
    fig.update_yaxes(title_text="", tickfont=dict(color=INK_2))
    return base_layout(fig, title, subtitle, height=max(320, 30 * len(d) + 130))


# =============================================================================
# 2. Barres empilées à 100 % (part de chaque catégorie)
# =============================================================================
def share_bars(df: pd.DataFrame, row_col: str, part_col: str, value_col: str,
               colors: dict, labels: dict, title: str, subtitle: str = "") -> go.Figure:
    """Une barre par ligne, découpée en parts (%). `labels` : code -> texte affiché."""
    pivot = df.pivot_table(index=row_col, columns=part_col, values=value_col,
                           aggfunc="sum", fill_value=0, observed=True)
    share = pivot.div(pivot.sum(axis=1), axis=0) * 100
    fig = go.Figure()
    for part in [p for p in colors if p in share.columns]:
        fig.add_bar(
            y=[str(i) for i in share.index], x=share[part], orientation="h",
            name=labels.get(part, part), marker=dict(color=colors[part],
                                                    line=dict(color=SURFACE, width=2)),
            # Pas d'étiquette dans les segments trop étroits (valeur dans l'infobulle)
            text=[f"{v:.0f} %" if v >= 12 else "" for v in share[part]],
            textposition="inside", insidetextanchor="middle", textangle=0,
            textfont=dict(color="#FFFFFF"),
            customdata=pivot[part],
            hovertemplate="<b>%{y}</b><br>" + labels.get(part, part)
                          + " : %{x:.1f} % (%{customdata:,} )<extra></extra>",
        )
    fig.update_layout(barmode="stack", bargap=0.4)
    # Les % sont écrits dans les barres : pas besoin de graduations (évite le chevauchement avec la légende)
    fig.update_xaxes(range=[0, 100], showgrid=False, showticklabels=False)
    fig.update_yaxes(title_text="", tickfont=dict(color=INK_2))
    return base_layout(fig, title, subtitle, height=max(260, 60 * len(share) + 140))


# =============================================================================
# 3. Volcano plot : taille d'effet vs significativité
# =============================================================================
def volcano(df: pd.DataFrame, fdr_threshold: float, title: str, subtitle: str = "",
            labels: dict | None = None, max_points: int = 6000) -> go.Figure:
    """
    Axe x = taille d'effet (négatif = baisse), axe y = -log10(FDR) (haut = très significatif).
    `labels` : {'increase', 'decrease', 'x', 'y', 'threshold', 'effect'} -> textes traduits
    """
    labels = labels or {}
    d = df
    if len(d) > max_points:                       # échantillon pour garder l'app fluide
        top = d.nlargest(max_points // 2, "neg_log10_fdr")
        rest = d.drop(top.index).sample(max_points - len(top), random_state=42)
        d = pd.concat([top, rest])

    fig = go.Figure()
    for direction, color in [("decrease", DECREASE), ("increase", INCREASE)]:
        part = d[d["direction"] == direction]
        fig.add_scattergl(
            x=part["effect_size"], y=part["neg_log10_fdr"], mode="markers",
            name=labels.get(direction, direction),
            marker=dict(color=color, size=7, opacity=0.65, line=dict(color=SURFACE, width=1)),
            customdata=np.stack([np.asarray(part["effector"], dtype=object),
                                 np.asarray(part["feature"], dtype=object),
                                 part["fdr"]], axis=-1),
            hovertemplate="<b>%{customdata[0]}</b> → %{customdata[1]}<br>"
                          + labels.get("effect", "Effect") + " : %{x:.3f}<br>"
                          "FDR : %{customdata[2]:.2e}<extra></extra>",
        )
    y_thr = -np.log10(fdr_threshold)
    fig.add_hline(y=y_thr, line=dict(color=MUTED, width=1),
                  annotation_text=labels.get("threshold", f"FDR = {fdr_threshold}"),
                  annotation_position="top right", annotation_font_color=INK_2)
    fig.add_vline(x=0, line=dict(color=MUTED, width=1))
    fig.update_xaxes(title_text=labels.get("x", "Effect size"), range=[-1.05, 1.05])
    fig.update_yaxes(title_text=labels.get("y", "-log10(FDR)"))
    return base_layout(fig, title, subtitle, height=480)


# =============================================================================
# 4. Heatmap : facteurs x types de variables
# =============================================================================
def heatmap(matrix: pd.DataFrame, title: str, subtitle: str = "", value_name: str = "",
            diverging: bool = False, value_format: str = ",.0f") -> go.Figure:
    """Matrice (lignes = facteurs, colonnes = familles de variables)."""
    z = matrix.values
    if diverging:
        lim = float(np.nanmax(np.abs(z))) or 1.0
        scale, zmin, zmax = DIVERGING, -lim, lim
    else:
        scale = [[i / (len(SEQUENTIAL) - 1), c] for i, c in enumerate(SEQUENTIAL)]
        zmin, zmax = 0, float(np.nanmax(z)) if np.size(z) else 1
    fig = go.Figure(go.Heatmap(
        z=z, x=[str(c) for c in matrix.columns], y=[str(i) for i in matrix.index],
        colorscale=scale, zmin=zmin, zmax=zmax, xgap=2, ygap=2,
        colorbar=dict(title=dict(text=value_name, font=dict(color=INK_2)), thickness=12,
                      tickfont=dict(color=MUTED), outlinewidth=0),
        hovertemplate="<b>%{y}</b> · %{x}<br>" + value_name + " : %{z:" + value_format
                      + "}<extra></extra>",
    ))
    fig.update_xaxes(showgrid=False, tickangle=-35, tickfont=dict(color=INK_2))
    fig.update_yaxes(showgrid=False, autorange="reversed", tickfont=dict(color=INK_2))
    return base_layout(fig, title, subtitle, height=max(360, 26 * len(matrix) + 170))


# =============================================================================
# 5. Carte : patients par pays (contours des pays chargés par le navigateur depuis Plotly)
# =============================================================================
COUNTRY_ISO3 = {"France": "FRA", "Germany": "DEU", "Danemark": "DNK", "Denmark": "DNK"}


def country_map(df: pd.DataFrame, country_col: str, value_col: str, title: str,
                subtitle: str = "", value_name: str = "", names: dict | None = None) -> go.Figure:
    """Choroplèthe européenne (une seule teinte : plus foncé = plus de patients)."""
    d = df.copy()
    d["iso3"] = d[country_col].map(COUNTRY_ISO3)
    d["name"] = d[country_col].map(names or {}).fillna(d[country_col])
    scale = [[i / (len(SEQUENTIAL) - 1), c] for i, c in enumerate(SEQUENTIAL)]
    fig = go.Figure(go.Choropleth(
        locations=d["iso3"], z=d[value_col], text=d["name"], colorscale=scale, zmin=0,
        marker_line_color=SURFACE, marker_line_width=1,
        colorbar=dict(title=dict(text=value_name, font=dict(color=INK_2)), thickness=12,
                      tickfont=dict(color=MUTED), outlinewidth=0),
        hovertemplate="<b>%{text}</b><br>" + value_name + " : %{z:,}<extra></extra>",
    ))
    fig.update_geos(scope="europe", projection_type="mercator",
                    lataxis_range=[42, 59], lonaxis_range=[-6, 20],
                    showcountries=True, countrycolor=GRID, showland=True, landcolor=NEUTRAL,
                    showocean=False, showlakes=False, showframe=False, bgcolor=SURFACE)
    return base_layout(fig, title, subtitle, height=440)


# =============================================================================
# 6. Réseau médicaments -> variables
# =============================================================================
def network_figure(G: nx.Graph, title: str, subtitle: str = "",
                   class_labels: dict | None = None, drug_label: str = "Drug",
                   hover_labels: dict | None = None) -> go.Figure:
    """
    Dessine un graphe biparti : losanges bleus = médicaments, autres formes = variables.
    Arêtes : rouge = hausse, bleu = baisse.
    Disposition radiale (utils.network.radial_layout) : même image à chaque lancement.
    """
    from utils.network import radial_layout
    class_labels = class_labels or {}
    hover_labels = hover_labels or {}
    linked_drugs = hover_labels.get("linked_drugs", "Linked drugs")
    linked_features = hover_labels.get("linked_features", "Linked features")
    pos = radial_layout(G)
    fig = go.Figure()

    # Arêtes : une trace par direction (plus rapide qu'une trace par arête)
    for direction, color in [("decrease", DECREASE), ("increase", INCREASE)]:
        xs, ys = [], []
        for u, v, data in G.edges(data=True):
            if data["direction"] == direction:
                xs += [pos[u][0], pos[v][0], None]
                ys += [pos[u][1], pos[v][1], None]
        fig.add_scatter(x=xs, y=ys, mode="lines", hoverinfo="skip", showlegend=False,
                        line=dict(color=color, width=1.2), opacity=0.45)

    # Nœuds variables, groupés par type (couleur + forme)
    for cls, color in CLASS_COLORS.items():
        nodes = [n for n, d in G.nodes(data=True) if d["kind"] == "feature" and d["cls"] == cls]
        if not nodes:
            continue
        fig.add_scatter(
            x=[pos[n][0] for n in nodes], y=[pos[n][1] for n in nodes], mode="markers",
            name=class_labels.get(cls, cls),
            marker=dict(color=color, symbol=CLASS_SYMBOLS[cls],
                        size=[8 + 3 * G.degree(n) for n in nodes],
                        line=dict(color=SURFACE, width=2)),
            text=[G.nodes[n]["label"] for n in nodes],
            customdata=[G.degree(n) for n in nodes],
            hovertemplate="<b>%{text}</b><br>" + class_labels.get(cls, cls)
                          + f"<br>{linked_drugs} : %{{customdata}}<extra></extra>",
        )

    # Nœuds médicaments, avec leur nom écrit (étiquettes directes)
    drugs = [n for n, d in G.nodes(data=True) if d["kind"] == "drug"]
    fig.add_scatter(
        x=[pos[n][0] for n in drugs], y=[pos[n][1] for n in drugs], mode="markers",
        name=drug_label,
        marker=dict(color=KIND_COLORS["drug"], symbol="diamond",
                    size=[14 + 1.2 * np.sqrt(G.degree(n)) * 3 for n in drugs],
                    line=dict(color=SURFACE, width=2)),
        text=[G.nodes[n]["label"] for n in drugs],
        customdata=[G.degree(n) for n in drugs],
        hovertemplate=f"<b>%{{text}}</b><br>{linked_features} : %{{customdata}}<extra></extra>",
    )
    # Noms des médicaments écrits au-delà de leur éventail (étiquettes directes)
    for n in drugs:
        x, y = pos[n]
        # Ancrage selon le côté du cercle : le texte part vers l'extérieur, jamais sur les nœuds
        xanchor = "left" if x > 0.3 else "right" if x < -0.3 else "center"
        yanchor = "bottom" if y > 0.3 else "top" if y < -0.3 else "middle"
        fig.add_annotation(x=x * 1.6, y=y * 1.6, text=f"<b>{G.nodes[n]['label']}</b>",
                           showarrow=False, font=dict(color=INK, size=12),
                           xanchor=xanchor, yanchor=yanchor)
    fig.update_xaxes(visible=False, range=[-2.1, 2.1])
    fig.update_yaxes(visible=False, range=[-2.0, 2.0], scaleanchor="x")
    return base_layout(fig, title, subtitle, height=680)
