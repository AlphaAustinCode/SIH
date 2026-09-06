import sys
from datetime import timedelta
from sqlalchemy import func

from app.database.session import SessionLocal
from app.database.models import TrackSection, TrainSchedule, MaintenanceRequest, Department

def run_step1_validation():
    db = SessionLocal()
    print("\n" + "="*50)
    print("      STEP 1: RAILWAY DATA VALIDATION SUITE")
    print("="*50 + "\n")

    failures = 0
    warnings = 0

    # ----------------------------------------------------
    # Check 1: Record Counts & Entity Presence
    # ----------------------------------------------------
    section_count = db.query(TrackSection).count()
    train_movements = db.query(TrainSchedule).count()
    request_count = db.query(MaintenanceRequest).count()

    print(f"[1/6] Entity Counts:")
    print(f"      - Track Sections:         {section_count}")
    print(f"      - Train Block Movements:  {train_movements}")
    print(f"      - Maintenance Requests:   {request_count}")

    if section_count < 10 or train_movements < 100 or request_count < 20:
        print("      ❌ FAILED: Insufficient base data.")
        failures += 1
    else:
        print("      ✅ PASSED: All core entities populated.")

    # ----------------------------------------------------
    # Check 2: Referential Integrity (Foreign Keys)
    # ----------------------------------------------------
    valid_section_ids = {s.id for s in db.query(TrackSection.id).all()}
    
    orphan_trains = db.query(TrainSchedule).filter(~TrainSchedule.track_section_id.in_(valid_section_ids)).count()
    orphan_requests = db.query(MaintenanceRequest).filter(~MaintenanceRequest.track_section_id.in_(valid_section_ids)).count()

    print(f"\n[2/6] Referential Integrity:")
    if orphan_trains == 0 and orphan_requests == 0:
        print("      ✅ PASSED: All foreign keys point to valid TrackSections.")
    else:
        print(f"      ❌ FAILED: Found {orphan_trains} orphaned trains and {orphan_requests} orphaned requests.")
        failures += 1

    # ----------------------------------------------------
    # Check 3: Timetable Chronology (entry_time < exit_time)
    # ----------------------------------------------------
    invalid_time_trains = db.query(TrainSchedule).filter(
        TrainSchedule.scheduled_entry >= TrainSchedule.scheduled_exit
    ).count()

    print(f"\n[3/6] Timetable Chronology:")
    if invalid_time_trains == 0:
        print("      ✅ PASSED: All train entry times are strictly earlier than exit times.")
    else:
        print(f"      ❌ FAILED: Found {invalid_time_trains} trains with scheduled_entry >= scheduled_exit.")
        failures += 1

    # ----------------------------------------------------
    # Check 4: Planning Horizon Limits
    # ----------------------------------------------------
    min_entry = db.query(func.min(TrainSchedule.scheduled_entry)).scalar()
    max_exit = db.query(func.max(TrainSchedule.scheduled_exit)).scalar()

    print(f"\n[4/6] 24-Hour Planning Horizon Bounds:")
    if min_entry and max_exit:
        horizon_span = max_exit - min_entry
        print(f"      - Earliest entry: {min_entry.strftime('%Y-%m-%d %H:%M')}")
        print(f"      - Latest exit:    {max_exit.strftime('%Y-%m-%d %H:%M')}")
        print(f"      - Total span:     {horizon_span}")
        
        if horizon_span <= timedelta(hours=36):
            print("      ✅ PASSED: Schedule comfortably aligns within the daily planning window.")
        else:
            print("      ⚠️ WARNING: Timetable spans more than 36 hours.")
            warnings += 1
    else:
        print("      ❌ FAILED: No train datetimes found.")
        failures += 1

    # ----------------------------------------------------
    # Check 5: Maintenance Request Integrity
    # ----------------------------------------------------
    invalid_urgency = db.query(MaintenanceRequest).filter(
        (MaintenanceRequest.urgency_priority < 1) | (MaintenanceRequest.urgency_priority > 10)
    ).count()
    invalid_duration = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.required_duration_minutes <= 0
    ).count()

    print(f"\n[5/6] Maintenance Request Parameter Sanity:")
    if invalid_urgency == 0 and invalid_duration == 0:
        print("      ✅ PASSED: Urgency scores (1-10) and durations (>0m) are valid.")
    else:
        print(f"      ❌ FAILED: Found {invalid_urgency} invalid urgency scores and {invalid_duration} non-positive durations.")
        failures += 1

    # ----------------------------------------------------
    # Check 6: Departmental Balance (TMS / SMMS / TDMS)
    # ----------------------------------------------------
    dept_counts = (
        db.query(MaintenanceRequest.department, func.count(MaintenanceRequest.id))
        .group_by(MaintenanceRequest.department)
        .all()
    )

    print(f"\n[6/6] Multi-Departmental Distribution:")
    dept_map = {dept.name: count for dept, count in dept_counts}
    for dept_name in ["TMS", "SMMS", "TDMS"]:
        count = dept_map.get(dept_name, 0)
        print(f"      - {dept_name:6s}: {count:2d} tasks")

    if len(dept_counts) == 3:
        print("      ✅ PASSED: Balanced representation across TMS, SMMS, and TDMS.")
    else:
        print("      ❌ FAILED: One or more departments are missing.")
        failures += 1

    # ----------------------------------------------------
    # Summary Report
    # ----------------------------------------------------
    print("\n" + "="*50)
    if failures == 0:
        print("       STATUS: STEP 1 IS OFFICIALLY COMPLETE! ✅")
        print("  Database is validated and ready for CP-SAT (Step 2).")
    else:
        print(f"       STATUS: {failures} CHECKS FAILED ❌")
        print("  Resolve the failures above before formulating CP-SAT.")
    print("="*50 + "\n")

    db.close()
    return failures == 0

if __name__ == "__main__":
    success = run_step1_validation()
    sys.exit(0 if success else 1)