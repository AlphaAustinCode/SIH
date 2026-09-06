import unittest

from app.main import app


class ApiContractTests(unittest.TestCase):
    def test_required_routes_are_registered(self):
        paths = set(app.openapi()["paths"])
        self.assertTrue(
            {
                "/api/optimization/run",
                "/api/optimization/latest",
                "/api/blocks",
                "/api/kpis",
                "/api/maintenance",
            }.issubset(paths)
        )

    def test_health_route_exists(self):
        self.assertIn("/health", app.openapi()["paths"])


if __name__ == "__main__":
    unittest.main()
