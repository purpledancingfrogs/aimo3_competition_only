from agents.nt_solver import NTSolver
from agents.alg_solver import AlgSolver
from agents.geo_solver import GeoSolver
from agents.comb_solver import CombSolver

def load_solvers():
    return {
        "NT": [NTSolver()],
        "ALG": [AlgSolver()],
        "GEO": [GeoSolver()],
        "COMB": [CombSolver()],
    }
