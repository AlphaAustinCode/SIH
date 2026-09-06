# scripts/run_optimizer.py
import sys
import os
# Force Python to recognize the root project folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from datetime import datetime
from app.database import init_db
from app.database.models import AllocatedBlock, MaintenanceRequest, TrackSection, TrainSchedule
from app.database.session import SessionLocal
from app.services.engine import IntegratedBlockOptimizer

def main():
    init_db()
    db = SessionLocal()
    
    train_count = db.query(TrainSchedule).count()
    task_count = db.query(MaintenanceRequest).count()
    sec_count = db.query(TrackSection).count()

    print("\n" + "="*80)
    print("   WESTERN RAILWAY (MUMBAI DIVISION) - AI BLOCK OPTIMIZER")
    print("      Production Step 2 Engine (Compatibility Enforced)")
    print("="*80)
    print(f" Datapoints Loaded: {sec_count} Track Sections | {train_count} Train Movements")
    print("="*80 + "\n")

    # Baseline: Siloed Schedule Calculation 
    all_requests = db.query(MaintenanceRequest).all()
    siloed_blocks_count = len(all_requests)
    siloed_possession_mins = sum(r.required_duration_minutes for r in all_requests)

    print(f"[1/3] Compiling Constraints & Running CP-SAT Solver for {task_count} Tasks...")
    
    optimizer = IntegratedBlockOptimizer(db=db)
    result = optimizer.optimize()

    if result["status"] not in ["OPTIMAL", "FEASIBLE"]:
        print(f"\n❌ Solver Failed! Status: {result['status']}")
        sys.exit(1)

    print(f"[2/3] Optimization Completed in {result['wall_time']:.3f}s with status: {result['status']}")
    print(f"      - Tasks Scheduled: {result['scheduled_count']} / {result.get('total_tasks', siloed_blocks_count)}\n")

    print("[3/3] Generating KPIs & Corridor Schedule...\n")
    blocks = db.query(AllocatedBlock).order_by(AllocatedBlock.start_time).all()

    integrated_possession_mins = 0
    clustered_blocks_count = 0

    print(f"{'BLK ID':<8}{'SECTION':<25}{'WINDOW':<16}{'TASKS':<7}{'DEPARTMENTS'}")
    print("-" * 80)

    for b in blocks:
        sec = db.query(TrackSection).filter(TrackSection.id == b.track_section_id).first()
        sec_name = sec.section_name if sec else f"Sec {b.track_section_id}"
        time_str = f"{b.start_time.strftime('%H:%M')}-{b.end_time.strftime('%H:%M')}"
        task_count_b = len(b.maintenance_requests)
        dept_str = ", ".join(list({t.department.name for t in b.maintenance_requests}))
        
        block_dur = int((b.end_time - b.start_time).total_seconds() / 60)
        integrated_possession_mins += block_dur

        if task_count_b > 1:
            clustered_blocks_count += 1
            highlight = " ★ [INTEGRATED]"
        else:
            highlight = ""

        print(f"B-{b.id:<6}{sec_name:<25}{time_str:<16}{task_count_b:<7}{dept_str}{highlight}")

    # Compute KPI Savings
    time_saved = siloed_possession_mins - integrated_possession_mins
    savings_pct = (time_saved / siloed_possession_mins * 100) if siloed_possession_mins > 0 else 0
    block_reduction = siloed_blocks_count - len(blocks)
    block_reduct_pct = (block_reduction / siloed_blocks_count * 100) if siloed_blocks_count > 0 else 0

    print("\n" + "="*80)
    print("                  BEFORE VS AFTER OPTIMIZATION (KPIs)")
    print("="*80)
    print(f" [BEFORE] Siloed Baseline:")
    print(f"   • Maintenance Interventions : {siloed_blocks_count} separate blocks")
    print(f"   • Total Track Possession    : {siloed_possession_mins} mins ({siloed_possession_mins/60:.1f} hrs)")
    print("")
    print(f" [AFTER] AI Integration:")
    print(f"   • Optimized Blocks          : {len(blocks)} unified blocks")
    print(f"   • Total Track Possession    : {integrated_possession_mins} mins ({integrated_possession_mins/60:.1f} hrs)")
    print("")
    print(f" [OPERATIONAL IMPACT]")
    print(f"   • Block Count Reduction       : -{block_reduction} interventions (-{block_reduct_pct:.1f}%)")
    print(f"   • Track Possession Reduced    : {time_saved} mins ({time_saved/60:.1f} hrs) saved (+{savings_pct:.1f}%)")
    print(f"   • Modelled Train Conflicts    : 0 (under implemented section-level constraints)")
    print("="*80 + "\n")

    db.close()

if __name__ == "__main__":
    main()