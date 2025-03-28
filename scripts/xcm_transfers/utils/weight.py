class Weight:
    ref_time: int
    proof_size: int

    def __init__(self, data):
        self.ref_time = data["ref_time"]
        self.proof_size = data["proof_size"]

    def is_max_by_any_dimension(self) -> bool:
        return self.ref_time >= self.max_dimension() or self.proof_size >= self.max_dimension()

    @staticmethod
    def max_dimension():
        return 18_446_744_073_709_551_615