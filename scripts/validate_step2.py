# scripts/validate_step2.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from datetime import timedelta
from sqlalchemy import func
from app.database import init_db
from app.database.models import AllocatedBlock, MaintenanceRequest, TrainSchedule, Department
from app.database.session import SessionLocal
from app.services.engine import COMPATIBILITY_MATRIX, SAFETY_BUFFER_MINS

def validate_optimization():
    init_db()
    db = SessionLocal()
    print("\n" + "="*70)
    print("      STEP 2: CP-SAT OUTPUT VALIDATION SUITE")
    print("="*70 + "\n")

    failures = 0
    blocks = db.query(AllocatedBlock).all()
    all_requests = db.query(MaintenanceRequest).all()
    
    if not blocks:
        print("❌ FAILED: No AllocatedBlocks found. Run optimizer first.")
        sys.exit(1)

    min_time = db.query(func.min(TrainSchedule.scheduled_entry)).scalar()
    max_time = db.query(func.max(TrainSchedule.scheduled_exit)).scalar()
    base_date = min_time.replace(hour=0, minute=0, second=0, microsecond=0)
    absolute_end = base_date + timedelta(minutes=int((max_time - base_date).total_seconds() / 60) + 180)

    # 1. Coverage
    scheduled_task_ids = {t.id for b in blocks for t in b.maintenance_requests}
    all_task_ids = {t.id for t in all_requests}
    unscheduled = all_task_ids - scheduled_task_ids
    
    print(f"[1/5] Task Coverage:")
    if not unscheduled:
        print("      ✅ PASSED: 100% of Maintenance Requests are scheduled.")
    else:
        print(f"      ❌ FAILED: {len(unscheduled)} tasks were dropped by the solver.")
        failures += 1

    # 2. Duration
    duration_errors = 0
    for b in blocks:
        block_dur_mins = (b.end_time - b.start_time).total_seconds() / 60
        max_task_dur = max([t.required_duration_minutes for t in b.maintenance_requests], default=0)
        if block_dur_mins < max_task_dur:
            duration_errors += 1
            
    print(f"\n[2/5] Block Duration Logic:")
    if duration_errors == 0:
        print("      ✅ PASSED: All integrated blocks properly encompass their task durations.")
    else:
        print(f"      ❌ FAILED: {duration_errors} blocks are too short for their assigned tasks.")
        failures += 1

    # 3. Compatibility
    compatibility_errors = 0
    for b in blocks:
        if len(b.maintenance_requests) > 1:
            depts = [t.department.name for t in b.maintenance_requests]
            for i in range(len(depts)):
                for j in range(i + 1, len(depts)):
                    d1, d2 = depts[i], depts[j]
                    is_compat = COMPATIBILITY_MATRIX.get((d1, d2), False) or COMPATIBILITY_MATRIX.get((d2, d1), False)
                    if not is_compat:
                        compatibility_errors += 1

    print(f"\n[3/5] Department Compatibility:")
    if compatibility_errors == 0:
        print("      ✅ PASSED: All clustered tasks respect the compatibility matrix.")
    else:
        print(f"      ❌ FAILED: {compatibility_errors} instances of incompatible tasks forced together.")
        failures += 1

    # 4. Collisions
    overlap_errors = 0
    for b in blocks:
        if not any(t.traffic_block_required for t in b.maintenance_requests):
            continue
            
        b_start = b.start_time - timedelta(minutes=SAFETY_BUFFER_MINS)
        b_end = b.end_time + timedelta(minutes=SAFETY_BUFFER_MINS)
        
        trains = db.query(TrainSchedule).filter(TrainSchedule.track_section_id == b.track_section_id).all()
        for tr in trains:
            if b_start < tr.scheduled_exit and tr.scheduled_entry < b_end:
                overlap_errors += 1
                
    print(f"\n[4/5] Train Collision Avoidance:")
    if overlap_errors == 0:
        print("      ✅ PASSED: Zero overlaps detected across train movements.")
    else:
        print(f"      ❌ FAILED: {overlap_errors} hard safety constraint violations detected.")
        failures += 1

    # 5. Horizon Bounds
    horizon_errors = sum(1 for b in blocks if b.start_time < base_date or b.end_time > absolute_end)
                
    print(f"\n[5/5] Planning Horizon Bounds:")
    if horizon_errors == 0:
        print("      ✅ PASSED: All maintenance blocks fit safely inside the temporal horizon.")
    else:
        print(f"      ❌ FAILED: {horizon_errors} blocks slipped outside the allowed time window.")
        failures += 1

    print("\n" + "="*70)
    if failures == 0:
        print("       STATUS: STEP 2 IS OFFICIALLY COMPLETE! ✅")
        print("  Algorithm logic verified. Ready for Step 3 (FastAPI/React).")
    else:
        print(f"       STATUS: {failures} TESTS FAILED ❌")
    print("="*70 + "\n")

    db.close()
    return failures == 0

if __name__ == "__main__":
    success = validate_optimization()
    sys.exit(0 if success else 1)