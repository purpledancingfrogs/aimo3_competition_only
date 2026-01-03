# Base class for all solvers

class SolverBase:
    domain = None

    def solve(self, problem_text):
        raise NotImplementedError
