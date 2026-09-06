from __future__ import annotations

import random
from datetime import datetime, timedelta

from app.database import init_db
from app.database.models import (
    AllocatedBlock,
    Department,
    LineType,
    MaintenanceRequest,
    MaintenanceStatus,
    TrackSection,
    TrainSchedule,
)
from app.database.session import SessionLocal


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DATE = datetime(2026, 9, 1, 0, 0, 0)

random.seed(42)


# ============================================================
# CORRIDOR DATA
# ============================================================

CORRIDOR_SECTIONS = [
    {
        "name": "CSMT-Dadar",
        "start": "CSMT",
        "end": "DR",
        "start_km": 0.0,
        "end_km": 9.0,
        "speed": 80,
    },
    {
        "name": "Dadar-Kurla",
        "start": "DR",
        "end": "CLA",
        "start_km": 9.0,
        "end_km": 18.0,
        "speed": 80,
    },
    {
        "name": "Kurla-Thane",
        "start": "CLA",
        "end": "TNA",
        "start_km": 18.0,
        "end_km": 34.0,
        "speed": 100,
    },
    {
        "name": "Thane-Kalyan",
        "start": "TNA",
        "end": "KYN",
        "start_km": 34.0,
        "end_km": 54.0,
        "speed": 110,
    },
    {
        "name": "Kalyan-Dombivli",
        "start": "KYN",
        "end": "DI",
        "start_km": 54.0,
        "end_km": 65.0,
        "speed": 110,
    },
    {
        "name": "Kalyan-Karjat",
        "start": "KYN",
        "end": "KJT",
        "start_km": 65.0,
        "end_km": 100.0,
        "speed": 110,
    },
]


# ============================================================
# TRAIN DATA
# ============================================================

TRAINS = [
    ("22120", "Tejas Express", 1),
    ("22221", "Rajdhani Express", 1),
    ("22222", "Rajdhani Express", 1),
    ("11010", "Sinhagad Express", 2),
    ("11007", "Deccan Express", 2),
    ("12123", "Deccan Queen", 1),
    ("12124", "Deccan Queen", 1),
    ("11029", "Koyna Express", 2),
    ("11019", "Konark Express", 2),
    ("12135", "Pune Nagpur Express", 2),
    ("12128", "Intercity Express", 2),
    ("11077", "Jhelum Express", 2),
    ("12133", "Mangaluru Express", 2),
    ("12137", "Punjab Mail", 2),
    ("11055", "Godan Express", 2),
    ("22158", "Superfast Express", 2),
    ("90001", "Suburban Fast Service", 2),
    ("90002", "Suburban Fast Service", 2),
    ("FRT001", "Container Freight Service", 3),
    ("FRT002", "Goods Freight Service", 3),
]


# ============================================================
# MAINTENANCE TASK DEFINITIONS
# ============================================================

TMS_TASKS = [
    ("Rail Weld", "Aluminothermic weld inspection and defect rectification"),
    ("Track Geometry", "Track geometry measurement and corrective maintenance"),
    ("Turnout", "Points and crossing inspection"),
    ("Rail Grinding", "Rail head surface defect treatment"),
    ("Ballast Packing", "Ballast packing and track stabilization"),
    ("Fish Plate", "Fish plate and fastening inspection"),
    ("Rail Replacement", "Localized rail replacement due to wear"),
    ("Tamping", "Machine tamping and track alignment correction"),
]

SMMS_TASKS = [
    ("Track Circuit", "Track circuit insulation resistance testing"),
    ("Point Machine", "Point machine preventive maintenance"),
    ("Axle Counter", "Axle counter reset and calibration"),
    ("Signal Relay", "Signal relay room preventive maintenance"),
    ("Signal Cable", "Signal cable continuity testing"),
    ("LED Signal", "Signal aspect verification and replacement"),
    ("Interlocking", "Electronic interlocking health check"),
]

TDMS_TASKS = [
    ("OHE", "Overhead equipment inspection and adjustment"),
    ("Pantograph Contact Wire", "Contact wire wear inspection"),
    ("Section Insulator", "Section insulator preventive maintenance"),
    ("OHE Mast", "OHE mast structural inspection"),
    ("Neutral Section", "Neutral section inspection"),
    ("Feeder Cable", "Traction feeder cable inspection"),
    ("Circuit Breaker", "Traction power circuit breaker maintenance"),
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_track_sections(db) -> list[TrackSection]:
    """
    Create UP, DOWN and LOOP track sections
    for the synthetic Mumbai-Karjat corridor.
    """

    created_sections: list[TrackSection] = []

    for section in CORRIDOR_SECTIONS:

        for line_type in [
            LineType.UP,
            LineType.DOWN,
            LineType.LOOP,
        ]:

            section_record = TrackSection(
                section_name=f"{section['name']} {line_type.value}",
                start_station_code=section["start"],
                end_station_code=section["end"],
                line_type=line_type,
                start_km=section["start_km"],
                end_km=section["end_km"],
                max_permissible_speed=section["speed"],
            )

            db.add(section_record)
            created_sections.append(section_record)

    db.commit()

    for section in created_sections:
        db.refresh(section)

    return created_sections


def create_train_schedules(
    db,
    sections: list[TrackSection],
) -> None:
    """
    Generate 20 synthetic train movements across
    the 24-hour planning horizon.
    """

    main_sections = [
        section
        for section in sections
        if section.line_type in {
            LineType.UP,
            LineType.DOWN,
        }
    ]

    for index, (
        train_number,
        train_name,
        priority,
    ) in enumerate(TRAINS):

        direction = (
            LineType.DOWN
            if index % 2 == 0
            else LineType.UP
        )

        matching_sections = [
            section
            for section in main_sections
            if section.line_type == direction
        ]

        start_hour = random.randint(0, 21)

        current_time = BASE_DATE + timedelta(
            hours=start_hour,
            minutes=random.randint(0, 50),
        )

        # Train traverses corridor sections.
        for section in matching_sections:

            travel_minutes = random.randint(8, 25)

            entry_time = current_time
            exit_time = entry_time + timedelta(
                minutes=travel_minutes
            )

            train_schedule = TrainSchedule(
                train_number=train_number,
                train_name=train_name,
                priority_level=priority,
                track_section_id=section.id,
                scheduled_entry=entry_time,
                scheduled_exit=exit_time,
                direction=direction,
            )

            db.add(train_schedule)

            dwell_minutes = random.randint(2, 8)

            current_time = (
                exit_time
                + timedelta(minutes=dwell_minutes)
            )

    db.commit()


def create_maintenance_requests(
    db,
    sections: list[TrackSection],
) -> None:
    """
    Generate exactly 35 realistic pending
    maintenance requests.
    """

    requests_created = 0

    department_distribution = (
        [Department.TMS] * 12
        + [Department.SMMS] * 12
        + [Department.TDMS] * 11
    )

    random.shuffle(department_distribution)

    for department in department_distribution:

        section = random.choice(sections)

        location_km = round(
            random.uniform(
                section.start_km,
                section.end_km,
            ),
            3,
        )

        if department == Department.TMS:

            asset_type, description = random.choice(
                TMS_TASKS
            )

            power_required = False

            duration = random.choice(
                [30, 45, 60, 90, 120]
            )

        elif department == Department.SMMS:

            asset_type, description = random.choice(
                SMMS_TASKS
            )

            power_required = random.choice(
                [False, False, True]
            )

            duration = random.choice(
                [20, 30, 45, 60]
            )

        else:

            asset_type, description = random.choice(
                TDMS_TASKS
            )

            power_required = True

            duration = random.choice(
                [30, 45, 60, 90]
            )

        traffic_block_required = random.choice(
            [True, True, True, False]
        )

        request = MaintenanceRequest(
            department=department,
            asset_type=asset_type,
            description=description,
            track_section_id=section.id,
            location_km=location_km,
            required_duration_minutes=duration,
            urgency_priority=random.randint(1, 5),
            power_isolation_required=power_required,
            traffic_block_required=traffic_block_required,
            status=MaintenanceStatus.PENDING,
        )

        db.add(request)

        requests_created += 1

    db.commit()

    print(
        f"Created {requests_created} maintenance requests."
    )


# ============================================================
# MAIN SEED FUNCTION
# ============================================================

def seed_database() -> None:

    init_db()

    db = SessionLocal()

    try:

        # Clear existing data in correct foreign-key order.
        db.query(MaintenanceRequest).delete()
        db.query(AllocatedBlock).delete()
        db.query(TrainSchedule).delete()
        db.query(TrackSection).delete()

        db.commit()

        print(
            "\n"
            "========================================\n"
            " SEEDING MUMBAI - KARJAT CORRIDOR\n"
            "========================================\n"
        )

        print("Creating track sections...")

        sections = create_track_sections(db)

        print(
            f"Created {len(sections)} track sections."
        )

        print("Creating train schedules...")

        create_train_schedules(
            db,
            sections,
        )

        train_count = db.query(
            TrainSchedule
        ).count()

        print(
            f"Created {train_count} train movements."
        )

        print(
            "Creating maintenance requests..."
        )

        create_maintenance_requests(
            db,
            sections,
        )

        maintenance_count = db.query(
            MaintenanceRequest
        ).count()

        print(
            f"Created {maintenance_count} "
            "maintenance requests."
        )

        print(
            "\n"
            "========================================\n"
            " DATABASE SEED COMPLETED SUCCESSFULLY\n"
            "========================================\n"
        )

    except Exception as exc:

        db.rollback()

        print(
            f"Database seeding failed: {exc}"
        )

        raise

    finally:

        db.close()


if __name__ == "__main__":
    seed_database()