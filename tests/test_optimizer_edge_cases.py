import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.models import (
    Department,
    LineType,
    MaintenanceRequest,
    TrackSection,
    TrainSchedule,
)
from app.services.engine import IntegratedBlockOptimizer


class OptimizerEdgeCaseTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        section = TrackSection(
            section_name="TEST-A-TEST-B",
            start_station_code="TESTA",
            end_station_code="TESTB",
            line_type=LineType.UP,
            start_km=0,
            end_km=2.5,
            max_permissible_speed=110,
        )
        self.session.add(section)
        self.session.flush()
        self.section = section
        self.session.add(
            TrainSchedule(
                train_number="T0",
                train_name="Horizon Train",
                priority_level=1,
                track_section_id=section.id,
                scheduled_entry=datetime(2026, 1, 1, 8),
                scheduled_exit=datetime(2026, 1, 1, 9),
                direction=LineType.UP,
            )
        )
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_no_tasks_returns_no_tasks(self):
        result = IntegratedBlockOptimizer(self.session).optimize()
        self.assertEqual(result["status"], "NO_TASKS")

    def test_compatible_tasks_are_scheduled(self):
        base = datetime(2026, 1, 1)
        self.session.add(
            TrainSchedule(
                train_number="T1",
                train_name="Test Train",
                priority_level=1,
                track_section_id=self.section.id,
                scheduled_entry=base + timedelta(hours=8),
                scheduled_exit=base + timedelta(hours=9),
                direction=LineType.UP,
            )
        )
        for department in (Department.TMS, Department.SMMS):
            self.session.add(
                MaintenanceRequest(
                    department=department,
                    asset_type="Test asset",
                    description="Test request",
                    track_section_id=self.section.id,
                    location_km=1,
                    required_duration_minutes=30,
                    urgency_priority=5,
                    traffic_block_required=False,
                )
            )
        self.session.commit()
        result = IntegratedBlockOptimizer(self.session).optimize()
        self.assertEqual(result["scheduled_count"], 2)
        self.assertGreaterEqual(result["blocks_created"], 1)


if __name__ == "__main__":
    unittest.main()
