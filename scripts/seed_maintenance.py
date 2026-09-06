import random

from app.database.session import SessionLocal
from app.database.models import TrackSection, MaintenanceRequest, Department, MaintenanceStatus

# Authentic Indian Railways Maintenance Task Catalog
TMS_TASKS = [
    ("USFD Rail Flaw Testing", 45, False, False),
    ("Ballast Tamping (DUOMAT)", 120, False, True),
    ("Turnout Rail Weld Inspection", 60, False, True),
    ("Glued Insulated Joint Replacement", 90, False, True),
    ("Through Sleeper Renewal (TSR)", 180, False, True),
]

SMMS_TASKS = [
    ("Point Machine Overhaul (Siemens/IRS)", 60, False, True),
    ("Track Circuit Bond Renewal", 30, False, True),
    ("Axle Counter Sensor Calibration", 45, False, True),
    ("Color Light Signal LED Replacement", 30, False, False),
    ("Interlocking Cable Insulation Testing", 60, False, True),
]

TDMS_TASKS = [
    ("Catenary & Contact Wire Adjustment", 120, True, True),
    ("Cantilever Assembly Replacement", 90, True, True),
    ("OHE Section Insulator Overhaul", 60, True, True),
    ("Neutral Section Inspection & Greasing", 60, True, True),
    ("Isolator Switch Contact Servicing", 45, True, True),
]

def seed_maintenance_requests(target_count: int = 35):
    db = SessionLocal()
    
    # 1. Clear existing maintenance requests
    deleted = db.query(MaintenanceRequest).delete()
    db.commit()
    print(f"Cleared {deleted} existing maintenance requests.")

    # 2. Fetch all valid TrackSections created in Step 1
    sections = db.query(TrackSection).all()
    if not sections:
        print("❌ Error: No TrackSections found! Run ingest_trains.py first.")
        db.close()
        return

    print(f"Found {len(sections)} TrackSections to anchor maintenance requests.")

    requests = []
    # Department allocation: ~13 TMS, ~11 SMMS, ~11 TDMS
    dept_distribution = (
        [(Department.TMS, TMS_TASKS)] * 13 +
        [(Department.SMMS, SMMS_TASKS)] * 11 +
        [(Department.TDMS, TDMS_TASKS)] * 11
    )
    random.shuffle(dept_distribution)

    for dept, task_list in dept_distribution[:target_count]:
        asset_name, duration, needs_power, needs_traffic = random.choice(task_list)
        section = random.choice(sections)

        # Place the exact chainage stone within the section bounds
        exact_km = round(random.uniform(section.start_km, section.end_km), 2)
        
        req = MaintenanceRequest(
            department=dept,
            asset_type=asset_name,
            description=f"Routine {asset_name}",
            track_section_id=section.id,
            location_km=exact_km,
            required_duration_minutes=duration,
            urgency_priority=random.randint(4, 10), # 10 being emergency/critical
            power_isolation_required=needs_power,
            traffic_block_required=needs_traffic,
            status=MaintenanceStatus.PENDING
        )
        requests.append(req)
        db.add(req)

    db.commit()
    print(f"✅ Successfully created and anchored {len(requests)} maintenance requests.")
    db.close()

if __name__ == "__main__":
    seed_maintenance_requests(35)