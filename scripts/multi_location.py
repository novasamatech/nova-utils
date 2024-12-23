from __future__ import annotations

from dataclasses import dataclass
from typing import List

# A class representing GlobalMultiLocations - a location that is represented from the root ancestry point of view
# Thus, it cannot have any parents and we separate it on type level from RelativeMultiLocation for better code safety
@dataclass
class GlobalMultiLocation:
    junctions: List[dict]

    def as_relative(self) -> RelativeMultiLocation:
        return RelativeMultiLocation(parents=0, junctions=self.junctions)

    # reanchor given location to a point of view of given `target` location
    def reanchor(self, target: GlobalMultiLocation) -> RelativeMultiLocation:
        common_ancestor_idx = self.find_last_common_junction_idx(target)
        if common_ancestor_idx is None:
            return RelativeMultiLocation(parents=len(target.junctions), junctions=self.junctions)

        parents = len(target.junctions) - (common_ancestor_idx+1)
        junctions = self.junctions[(common_ancestor_idx+1):]

        return RelativeMultiLocation(parents=parents, junctions=junctions)


    def find_last_common_junction_idx(self, other: GlobalMultiLocation) -> int | None:
        result = None

        for index in range(min(len(self.junctions), len(other.junctions))):
            self_junction = self.junctions[index]
            other_junction = other.junctions[index]

            if self_junction == other_junction:
                result = index
            else:
                break

        return result

@dataclass
class RelativeMultiLocation:
    parents: int
    junctions: List[dict]

    def __init__(self, parents: int, junctions: List[dict]):
        self.parents = parents
        self.junctions = junctions

def parachain_id(parachain_id: int) -> dict:
    return {"Parachain": parachain_id}
