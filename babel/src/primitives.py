"""
Semantic primitive taxonomy for cross-species communication.
These are the nodes of the BABEL graph.
"""

from dataclasses import dataclass, field
from typing import Optional


# The 9 functional primitives identified from comparative ethology literature
PRIMITIVES = {
    "ALARM_AERIAL": {
        "description": "Threat from above — raptor, drone, aerial predator",
        "known_signals": {
            "vervet_monkey": "high-pitched bark ('eagle call')",
            "prairie_dog": "jump-yip + whistle sequence",
            "crow": "rapid 'caw-caw-caw'",
            "meerkat": "high-pitched peep",
        },
        "literature": "Cheney & Seyfarth 1990; Slobodikoff 2009",
    },
    "ALARM_GROUND": {
        "description": "Threat at ground level — terrestrial predator",
        "known_signals": {
            "vervet_monkey": "low bark ('leopard call')",
            "prairie_dog": "bark + chuckle",
            "ground_squirrel": "repetitive chatters",
        },
        "literature": "Cheney & Seyfarth 1990",
    },
    "ALARM_SNAKE": {
        "description": "Cryptic ground threat — snake or slow-moving predator",
        "known_signals": {
            "vervet_monkey": "high chutter ('snake call')",
            "mongoose": "twitter call",
        },
        "literature": "Cheney & Seyfarth 1990",
    },
    "FOOD_CALL": {
        "description": "Food found — recruit others, signal food location",
        "known_signals": {
            "domestic_chicken": "food 'tuck-tuck' call",
            "crow": "assembly calls near food",
            "sperm_whale": "slow codas during feeding",
        },
        "literature": "Evans & Marler 1994",
    },
    "CONTACT_AFFILIATION": {
        "description": "Social bonding — maintain group cohesion, greeting",
        "known_signals": {
            "elephant": "rumbles (infrasound)",
            "bottlenose_dolphin": "signature whistle",
            "sperm_whale": "identity codas",
            "prairie_dog": "jump-yip (non-alarm context)",
        },
        "literature": "Poole et al. 2005; Tyack 1997",
    },
    "DISTRESS": {
        "description": "Pain, fear, isolation — negative valence signal",
        "known_signals": {
            "pig": "high-frequency squeal",
            "cow": "high-pitched moo",
            "vervet_monkey": "scream",
        },
        "literature": "Briefer et al. 2025 (Copenhagen study)",
    },
    "MATING": {
        "description": "Courtship, mate attraction, reproductive signaling",
        "known_signals": {
            "humpback_whale": "complex song (culturally transmitted)",
            "songbird": "species-specific song",
            "frog": "advertisement call",
        },
        "literature": "Garland et al. 2020",
    },
    "IDENTITY": {
        "description": "Individual recognition — 'name-like' signals",
        "known_signals": {
            "bottlenose_dolphin": "signature whistle (unique per individual)",
            "elephant": "name-like contact rumble",
            "sperm_whale": "individual coda pattern",
            "parrot": "learned contact call",
        },
        "literature": "Tyack 1997; Pardo et al. 2024",
    },
    "LOCATION": {
        "description": "Spatial information — where something is",
        "known_signals": {
            "prairie_dog": "encoded direction + distance in call shape",
            "honeybee": "waggle dance (non-vocal but communicative)",
            "bat": "echolocation return shared socially",
        },
        "literature": "Slobodikoff 2009; von Frisch 1967",
    },
}


@dataclass
class Signal:
    """A single recorded vocalization with metadata."""
    path: str
    species: str
    primitive: Optional[str] = None       # ground truth label if known
    confidence: float = 1.0               # 1.0 = human-labeled, <1.0 = inferred
    source_dataset: str = ""
    notes: str = ""
    embedding: Optional[object] = None    # filled by encoder


@dataclass
class PrimitiveNode:
    """A node in the BABEL semantic graph."""
    id: str
    description: str
    signals: list = field(default_factory=list)   # list of Signal objects
    known_signals: dict = field(default_factory=dict)

    @classmethod
    def from_registry(cls, primitive_id: str) -> "PrimitiveNode":
        data = PRIMITIVES[primitive_id]
        return cls(
            id=primitive_id,
            description=data["description"],
            known_signals=data.get("known_signals", {}),
        )


def get_all_primitives() -> list:
    return list(PRIMITIVES.keys())


def describe_primitive(pid: str) -> str:
    p = PRIMITIVES.get(pid, {})
    lines = [f"[{pid}] {p.get('description', '')}"]
    for species, signal in p.get("known_signals", {}).items():
        lines.append(f"  • {species}: {signal}")
    return "\n".join(lines)
