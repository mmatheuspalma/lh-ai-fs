from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


def _hay(flag: dict) -> str:
    """All searchable text for a flag, lowercased."""
    return " ".join(str(flag.get(k, "")) for k in
                     ("case_name", "quoted_text", "claim", "referent", "text")).lower()


def _has(flag: dict, *subs: str) -> bool:
    h = _hay(flag)
    return all(s.lower() in h for s in subs)


def _any(flag: dict, *subs: str) -> bool:
    h = _hay(flag)
    return any(s.lower() in h for s in subs)


@dataclass
class GoldEntry:
    id: str
    category: str          # citation | quote | fact
    description: str
    severity: str
    predicate: Callable[[dict], bool]

    def matches(self, flag: dict) -> bool:
        return flag.get("category") == self.category and self.predicate(flag)


# --- Known planted flaws (ground truth). Each should be caught by >=1 flag. ---
GOLD: list[GoldEntry] = [
    GoldEntry("privette_overstate", "citation",
              "Privette quote/cite overstates the holding (absolute 'never liable')",
              "high", lambda f: _has(f, "privette")),
    GoldEntry("privette_quote_overstated", "quote",
              "Direct Privette quote inserts an absolute 'never' the case does not hold",
              "high", lambda f: _any(f, "never", "privette")),
    GoldEntry("seabright_misattributed", "citation",
              "Seabright cited for a proposition it does not stand for",
              "high", lambda f: _has(f, "seabright")),
    GoldEntry("whitmore_fabricated", "citation",
              "Whitmore v. Delgado Scaffolding — unrecognizable, likely fabricated",
              "medium", lambda f: _has(f, "whitmore")),
    GoldEntry("kellerman_fabricated", "citation",
              "Kellerman v. Pacific Coast Construction — likely fabricated / overstated rule",
              "medium", lambda f: _has(f, "kellerman")),
    GoldEntry("wrong_jurisdiction", "citation",
              "Out-of-state cites (Dixon TX / Okafor FL) in a California matter",
              "medium", lambda f: _any(f, "dixon", "okafor", "lone star", "brightline")),
    GoldEntry("date_contradiction", "fact",
              "MSJ says incident March 14, 2021; record says March 12, 2021",
              "high", lambda f: _has(f, "march 14") or (_has(f, "date") and _has(f, "march 12"))),
    GoldEntry("ppe_contradiction", "fact",
              "MSJ says no PPE/fall-arrest; record says harness worn, anchor failed",
              "high", lambda f: _any(f, "protective equipment", "fall-arrest", "fall arrest",
                                     "harness", "ppe")),
]


# --- Negative controls: TRUE statements that must NOT be flagged. ---
NEGATIVE_CONTROLS: list[GoldEntry] = [
    GoldEntry("sol_correct", "citation",
              "CCP 335.1 two-year SOL is correctly stated — flagging it is a false positive",
              "n/a", lambda f: _any(f, "335.1", "statute of limitations")),
    GoldEntry("fall_height", "fact",
              "14-foot fall is consistent across documents — must not be flagged",
              "n/a", lambda f: _any(f, "14 feet", "fourteen feet", "14-foot")),
    GoldEntry("employer_role", "fact",
              "Apex was employer / Harmon general contractor — consistent across docs",
              "n/a", lambda f: _has(f, "apex") and _any(f, "employ", "subcontractor")),
]


def gold_by_id(gid: str) -> GoldEntry:
    for g in GOLD:
        if g.id == gid:
            return g
    raise KeyError(gid)
