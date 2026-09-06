# app/services/engine.py
import sys
import os
# Force Python to recognize the root project folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from ortools.sat.python import cp_model
from sqlalchemy.orm import Session
from sqlalchemy import func

# Smart import: Hunts for your DB models based on your folder structure
from app.database.models import (
    TrackSection,
    TrainSchedule,
    MaintenanceRequest,
    AllocatedBlock,
    BlockStatus,
    Department,
)

SAFETY_BUFFER_MINS = 5

COMPATIBILITY_MATRIX = {
    ("TMS", "SMMS"): True,
    ("SMMS", "TMS"): True,
    ("TDMS", "TMS"): True,
    ("TMS", "TDMS"): True,
    ("TDMS", "SMMS"): True,
    ("SMMS", "TDMS"): True,
    ("TMS", "TMS"): False,    
    ("SMMS", "SMMS"): False,  
    ("TDMS", "TDMS"): False,  
}

class IntegratedBlockOptimizer:
    def __init__(self, db: Session):
        self.db = db
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = 45.0 
        self.solver.parameters.num_workers = 8
        
        # Calculate planning horizon directly from the actual train timetable
        self.min_time = self.db.query(func.min(TrainSchedule.scheduled_entry)).scalar()
        self.max_time = self.db.query(func.max(TrainSchedule.scheduled_exit)).scalar()
        
        if not self.min_time or not self.max_time:
            raise ValueError("No train schedules found in DB to determine horizon.")
            
        self.base_date = self.min_time.replace(hour=0, minute=0, second=0, microsecond=0)
        self.horizon_minutes = int((self.max_time - self.base_date).total_seconds() / 60) + 180

    def _get_minute_offset(self, dt: datetime) -> int:
        return int((dt - self.base_date).total_seconds() // 60)

    def _get_datetime(self, minute_offset: int) -> datetime:
        return self.base_date + timedelta(minutes=minute_offset)

    def _precompute_busy_windows(self) -> Dict[int, List[Tuple[int, int]]]:
        raw_trains = self.db.query(TrainSchedule).all()
        section_busy_raw = defaultdict(list)

        for tr in raw_trains:
            s_min = max(0, self._get_minute_offset(tr.scheduled_entry) - SAFETY_BUFFER_MINS)
            e_min = min(self.horizon_minutes, self._get_minute_offset(tr.scheduled_exit) + SAFETY_BUFFER_MINS)
            if e_min > s_min:
                section_busy_raw[tr.track_section_id].append((s_min, e_min))

        merged_busy = {}
        for sec_id, intervals in section_busy_raw.items():
            intervals.sort(key=lambda x: x[0])
            merged = []
            for start, end in intervals:
                if not merged:
                    merged.append([start, end])
                else:
                    if start <= merged[-1][1]:
                        merged[-1][1] = max(merged[-1][1], end)
                    else:
                        merged.append([start, end])
            merged_busy[sec_id] = [(b[0], b[1]) for b in merged]

        return merged_busy

    def optimize(self) -> Dict[str, any]:
        tasks = self.db.query(MaintenanceRequest).all()
        if not tasks:
            return {"status": "NO_TASKS"}

        busy_windows = self._precompute_busy_windows()
        task_vars = {}

        # 1. Variables Definition (Mandatory Execution)
        for t in tasks:
            dur = t.required_duration_minutes
            start_v = self.model.NewIntVar(0, self.horizon_minutes - dur, f"start_{t.id}")
            end_v = self.model.NewIntVar(dur, self.horizon_minutes, f"end_{t.id}")
            interval_v = self.model.NewIntervalVar(start_v, dur, end_v, f"interval_{t.id}")

            task_vars[t.id] = {
                "start": start_v, "end": end_v, "interval": interval_v, "task": t, "dur": dur
            }

        # 2. Hard Constraints: No Conflict with Trains
        for t_id, tv in task_vars.items():
            sec_id = tv["task"].track_section_id
            sec_busy = busy_windows.get(sec_id, [])

            if tv["task"].traffic_block_required and sec_busy:
                fixed_train_intervals = []
                for idx, (b_start, b_end) in enumerate(sec_busy):
                    fixed_train_intervals.append(
                        self.model.NewFixedSizeIntervalVar(b_start, b_end - b_start, f"busy_{t_id}_{idx}")
                    )
                self.model.AddNoOverlap([tv["interval"]] + fixed_train_intervals)

        # 3. Hard Constraints: Department Compatibility & Soft Constraints: Clustering Bonus
        tasks_by_sec = defaultdict(list)
        for t_id, tv in task_vars.items():
            tasks_by_sec[tv["task"].track_section_id].append(tv)

        objective_terms = []

        for sec_id, sec_tasks in tasks_by_sec.items():
            if len(sec_tasks) > 1:
                for i in range(len(sec_tasks)):
                    for j in range(i + 1, len(sec_tasks)):
                        t1, t2 = sec_tasks[i], sec_tasks[j]
                        d1, d2 = t1["task"].department.name, t2["task"].department.name
                        
                        is_compatible = COMPATIBILITY_MATRIX.get((d1, d2), False) or COMPATIBILITY_MATRIX.get((d2, d1), False)
                        
                        if is_compatible:
                            # Soft constraint: reward overlap for compatible departments
                            overlap = self.model.NewBoolVar(f"overlap_{t1['task'].id}_{t2['task'].id}")
                            b1 = self.model.NewBoolVar(f"b1_{t1['task'].id}")
                            b2 = self.model.NewBoolVar(f"b2_{t2['task'].id}")

                            self.model.Add(t1["start"] < t2["end"]).OnlyEnforceIf(b1)
                            self.model.Add(t1["start"] >= t2["end"]).OnlyEnforceIf(b1.Not())
                            self.model.Add(t2["start"] < t1["end"]).OnlyEnforceIf(b2)
                            self.model.Add(t2["start"] >= t1["end"]).OnlyEnforceIf(b2.Not())

                            self.model.AddBoolAnd([b1, b2]).OnlyEnforceIf(overlap)
                            self.model.AddBoolOr([b1.Not(), b2.Not()]).OnlyEnforceIf(overlap.Not())
                            
                            objective_terms.append(overlap * 1000)
                        else:
                            # Hard constraint: incompatible tasks CANNOT overlap
                            self.model.AddNoOverlap([t1["interval"], t2["interval"]])

        # 4. Maximize early scheduling for urgent tasks
        for t_id, tv in task_vars.items():
            urgency = tv["task"].urgency_priority
            objective_terms.append(-tv["start"] * urgency)

        # Solve
        self.model.Maximize(sum(objective_terms))
        solver_status = self.solver.Solve(self.model)

        status_name = self.solver.StatusName(solver_status)
        if solver_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return {"status": status_name, "scheduled_count": 0, "blocks_created": 0}

        # 5. Commit AllocatedBlocks to Database
        self.db.query(AllocatedBlock).delete()
        self.db.commit()

        scheduled_tasks_by_sec = defaultdict(list)
        for t_id, tv in task_vars.items():
            scheduled_tasks_by_sec[tv["task"].track_section_id].append({
                "task": tv["task"],
                "start_m": self.solver.Value(tv["start"]),
                "end_m": self.solver.Value(tv["end"])
            })

        # Graceful fallback to DRAFT if OPTIMIZED doesn't exist
        block_status_enum = getattr(BlockStatus, "DRAFT", None)

        created_blocks = []
        for sec_id, task_list in scheduled_tasks_by_sec.items():
            task_list.sort(key=lambda x: x["start_m"])
            clusters = []
            
            for item in task_list:
                if not clusters:
                    clusters.append([item])
                else:
                    cluster_end = max(t["end_m"] for t in clusters[-1])
                    if item["start_m"] < cluster_end: 
                        clusters[-1].append(item)
                    else:
                        clusters.append([item])

            for cluster in clusters:
                block_start_min = min(t["start_m"] for t in cluster)
                block_end_min = max(t["end_m"] for t in cluster)

                alloc_block = AllocatedBlock(
                    track_section_id=sec_id,
                    start_time=self._get_datetime(block_start_min),
                    end_time=self._get_datetime(block_end_min),
                    status=block_status_enum
                )
                alloc_block.maintenance_requests = [t["task"] for t in cluster]
                self.db.add(alloc_block)
                created_blocks.append(alloc_block)

        self.db.commit()

        return {
            "status": status_name,
            "scheduled_count": len(tasks),
            "blocks_created": len(created_blocks),
            "wall_time": self.solver.WallTime(),
            "objective_value": self.solver.ObjectiveValue()
        }