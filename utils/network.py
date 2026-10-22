"""
Construction et analyse du réseau médicaments -> variables (microbiote, métabolome).

Séparé de viz.py : ici on CALCULE (graphe, centralité), viz.py ne fait que DESSINER.
"""
from __future__ import annotations

import math

import networkx as nx
import numpy as np
import pandas as pd

# Tests utilisés pour le réseau : effet de la prise d'un médicament (classe CMD).
# On évite de mélanger avec les doses / combinaisons / codes ATC, qui décrivent
# souvent le même médicament et créeraient des doublons dans le graphe.
NETWORK_TESTS = ["CMD drug intake effect"]


def network_edges(df: pd.DataFrame, top_drugs: int = 10, per_drug: int = 12) -> pd.DataFrame:
    """
    Sélectionne les arêtes à dessiner :
    - les `top_drugs` médicaments ayant le plus d'associations ;
    - pour chacun, ses `per_drug` associations les plus fortes (|effet|).
    `df` doit déjà être filtré (FDR, robustesse, groupe...).
    """
    d = df[df["test"].isin(NETWORK_TESTS)]
    if d.empty:
        return d
    top = d["effector"].value_counts().head(top_drugs).index
    d = d[d["effector"].isin(top)]
    d = (d.sort_values("abs_effect", ascending=False)
          .groupby("effector", observed=True).head(per_drug))
    return d.reset_index(drop=True)


def build_graph(edges: pd.DataFrame) -> nx.Graph:
    """Graphe biparti : nœuds 'drug:<nom>' et 'feat:<id>', une arête par association."""
    G = nx.Graph()
    for row in edges.itertuples(index=False):
        d_id, f_id = f"drug:{row.effector}", f"feat:{row.feature_space}|{row.feature_id}"
        G.add_node(d_id, kind="drug", label=str(row.effector))
        G.add_node(f_id, kind="feature", label=str(row.feature), cls=str(row.feature_class))
        G.add_edge(d_id, f_id, effect=float(row.effect_size), fdr=float(row.fdr),
                   direction=str(row.direction), weight=float(row.abs_effect))
    return G


def centrality_table(G: nx.Graph) -> pd.DataFrame:
    """
    Indicateurs par nœud :
    - degree : nombre de liens ;
    - betweenness : à quel point le nœud fait le « pont » entre d'autres
      (une variable touchée par plusieurs médicaments a une forte valeur).
    """
    if G.number_of_nodes() == 0:
        return pd.DataFrame(columns=["node", "label", "kind", "degree", "betweenness"])
    btw = nx.betweenness_centrality(G, normalized=True, seed=42)
    rows = [{"node": n, "label": d["label"], "kind": d["kind"], "cls": d.get("cls", ""),
             "degree": G.degree(n), "betweenness": round(btw[n], 4)}
            for n, d in G.nodes(data=True)]
    return pd.DataFrame(rows).sort_values(["degree", "betweenness"], ascending=False)


def shared_features(G: nx.Graph) -> pd.DataFrame:
    """Variables touchées par au moins 2 médicaments : les « carrefours » du réseau."""
    rows = []
    for n, d in G.nodes(data=True):
        if d["kind"] == "feature" and G.degree(n) >= 2:
            drugs = sorted(G.nodes[m]["label"] for m in G.neighbors(n))
            rows.append({"feature": d["label"], "class": d["cls"],
                         "n_drugs": len(drugs), "drugs": ", ".join(drugs)})
    return (pd.DataFrame(rows, columns=["feature", "class", "n_drugs", "drugs"])
            .sort_values("n_drugs", ascending=False).reset_index(drop=True))


def radial_layout(G: nx.Graph) -> dict:
    """
    Disposition lisible et reproductible (pas d'aléatoire) :
    - médicaments répartis sur un cercle (rayon 1), triés par nombre de liens ;
    - variables propres à un seul médicament : en éventail à l'extérieur de celui-ci ;
    - variables partagées par plusieurs médicaments : vers le centre, entre eux.
    Le centre du graphe montre donc les « carrefours » communs à plusieurs traitements.
    """
    drugs = sorted((n for n, d in G.nodes(data=True) if d["kind"] == "drug"),
                   key=lambda n: -G.degree(n))
    pos = {}
    for i, n in enumerate(drugs):
        angle = 2 * math.pi * i / max(len(drugs), 1) + math.pi / 2
        pos[n] = np.array([math.cos(angle), math.sin(angle)])

    private = {n: [] for n in drugs}
    shared = []
    for n, d in G.nodes(data=True):
        if d["kind"] != "feature":
            continue
        neighbors = list(G.neighbors(n))
        if len(neighbors) == 1:
            private[neighbors[0]].append(n)
        else:
            shared.append(n)

    # Variables propres : arc de cercle à l'extérieur du médicament
    for drug, feats in private.items():
        base = math.atan2(pos[drug][1], pos[drug][0])
        spread = min(math.pi / max(len(drugs), 2), 0.9)
        for j, f in enumerate(sorted(feats)):
            offset = (j / max(len(feats) - 1, 1) - 0.5) * spread if len(feats) > 1 else 0
            radius = 1.35 + 0.12 * (j % 2)           # deux rangées pour éviter les chevauchements
            pos[f] = radius * np.array([math.cos(base + offset), math.sin(base + offset)])

    # Variables partagées : barycentre des médicaments liés, ramené vers le centre
    for k, f in enumerate(sorted(shared)):
        center = np.mean([pos[m] for m in G.neighbors(f)], axis=0) * 0.55
        jitter = 0.07 * np.array([math.cos(k * 2.4), math.sin(k * 2.4)])   # angle d'or : pas de superposition
        pos[f] = center + jitter
    return pos
