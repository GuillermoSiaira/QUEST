"""
Semantic Primitive Graph — the core data structure of BABEL.
Nodes = communicative primitives. Edges = cross-species equivalences.
"""

import json
import networkx as nx
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path

from babel.src.primitives import PRIMITIVES, Signal


@dataclass
class GraphEdge:
    """Cross-species equivalence between two signals mapped to the same primitive."""
    species_a: str
    species_b: str
    primitive: str
    confidence: float        # 0–1, derived from literature strength
    literature_source: str = ""


class BabelGraph:
    """
    Bipartite knowledge graph:
      Layer 1: Semantic primitive nodes (ALARM_AERIAL, FOOD_CALL, ...)
      Layer 2: Species-signal nodes (vervet::eagle_call, prairie_dog::hawk_whistle, ...)
      Edges: signal → primitive (with confidence), primitive ↔ primitive (similarity)
    """

    def __init__(self):
        self.G = nx.Graph()
        self._init_primitive_nodes()

    def _init_primitive_nodes(self):
        for pid, data in PRIMITIVES.items():
            self.G.add_node(
                pid,
                node_type="primitive",
                description=data["description"],
                literature=data.get("literature", ""),
            )

    def add_signal(self, signal: Signal):
        """Add a species-signal node and connect it to its primitive."""
        node_id = f"{signal.species}::{Path(signal.path).stem}"
        self.G.add_node(
            node_id,
            node_type="signal",
            species=signal.species,
            path=signal.path,
            source_dataset=signal.source_dataset,
        )
        if signal.primitive and signal.primitive in PRIMITIVES:
            self.G.add_edge(
                node_id, signal.primitive,
                confidence=signal.confidence,
                edge_type="signal_to_primitive",
            )

    def add_cross_species_edge(self, edge: GraphEdge):
        """Add a direct cross-species equivalence (both signals on same primitive)."""
        self.G.add_edge(
            f"{edge.species_a}",
            f"{edge.species_b}",
            primitive=edge.primitive,
            confidence=edge.confidence,
            literature=edge.literature_source,
            edge_type="cross_species",
        )

    def query_primitive(self, primitive_id: str) -> dict:
        """Return all signals connected to a primitive, grouped by species."""
        neighbors = [
            (n, self.G.nodes[n])
            for n in self.G.neighbors(primitive_id)
            if self.G.nodes[n].get("node_type") == "signal"
        ]
        by_species = {}
        for node_id, attrs in neighbors:
            species = attrs.get("species", "unknown")
            by_species.setdefault(species, []).append(node_id)
        return by_species

    def find_equivalents(self, species: str, primitive: str) -> list:
        """
        Given a species and primitive, return signals from OTHER species
        that map to the same primitive. This is the R2-D2 lookup.
        """
        candidates = self.query_primitive(primitive)
        return {
            s: signals
            for s, signals in candidates.items()
            if s != species
        }

    def summary(self) -> dict:
        primitive_nodes = [n for n, d in self.G.nodes(data=True) if d.get("node_type") == "primitive"]
        signal_nodes = [n for n, d in self.G.nodes(data=True) if d.get("node_type") == "signal"]
        return {
            "primitives": len(primitive_nodes),
            "signals": len(signal_nodes),
            "edges": self.G.number_of_edges(),
            "species": list({
                self.G.nodes[n].get("species")
                for n in signal_nodes
                if self.G.nodes[n].get("species")
            }),
        }

    def save(self, path: Path):
        data = nx.node_link_data(self.G)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Graph saved: {path}")

    @classmethod
    def load(cls, path: Path) -> "BabelGraph":
        with open(path) as f:
            data = json.load(f)
        g = cls()
        g.G = nx.node_link_graph(data)
        return g
