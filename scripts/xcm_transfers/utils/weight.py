from __future__ import annotations

class Weight:
    ref_time: int
    proof_size: int

    def __init__(self, ref_time: int, proof_size: int):
        self.ref_time = ref_time
        self.proof_size = proof_size

    def is_max_by_any_dimension(self) -> bool:
        return self.ref_time >= self.max_dimension() or self.proof_size >= self.max_dimension()

    def to_sdk_value(self) -> dict:
        return {"ref_time": self.ref_time, "proof_size": self.proof_size}

    @staticmethod
    def max_dimension() -> int:
        return 18_446_744_073_709_551_615

    @staticmethod
    def from_sdk_value(sdk_value: dict) -> Weight:
        return Weight(sdk_value["ref_time"], sdk_value["proof_size"])

    @staticmethod
    def zero() -> Weight:
        return Weight(0, 0)
