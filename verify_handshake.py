import unittest
from unittest.mock import patch
import submission

class TestHybridHandoff(unittest.TestCase):

    def test_ladder_success(self):
        """Invariant: If Ladder works, Neural is sleeping."""
        res = submission.execute_with_safety("2+2")
        self.assertEqual(int(res), 4)

    @patch("submission.NeuralAgent")
    def test_neural_handoff(self, MockAgent):
        """Invariant: If Ladder fails, Neural wakes and code runs."""
        mock_instance = MockAgent.return_value
        mock_instance.generate_python_plan.return_value = """
print("Running Neural Code...")
primes = [2, 3, 5, 7]
print(sum(primes))
"""
        res = submission.execute_with_safety("Find the sum of primes below 10")
        self.assertEqual(int(res), 17)

    @patch("submission.NeuralAgent")
    def test_neural_crash_safety(self, MockAgent):
        """Invariant: If Neural code crashes, return 0."""
        mock_instance = MockAgent.return_value
        mock_instance.generate_python_plan.return_value = "print(1/0)"
        res = submission.execute_with_safety("Hard Problem")
        self.assertEqual(res, 0)

if __name__ == "__main__":
    unittest.main()