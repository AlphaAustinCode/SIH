import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Resolve project root for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database.session import SessionLocal
from app.database.models import (
    TrackSection, 
    TrainSchedule, 
    LineType, 
    AllocatedBlock, 
    MaintenanceRequest
)

BASE_DATE = datetime(2026, 9, 1, 0, 0, 0)

def ingest_western_railway():
    db = SessionLocal()
    
    print("Clearing old data in foreign-key safe order...")
    db.query(MaintenanceRequest).delete()
    db.query(AllocatedBlock).delete()
    db.query(TrainSchedule).delete()
    db.query(TrackSection).delete() 
    db.commit()

    section_map = {}
    current_chainage = 0.0 
    schedule_count = 0
    
    files = [
        ("Railway-1.json", "DN", "NORMAL"),
        ("Railway-2.json", "UP", "NORMAL"),
        ("Railway-3.json", "DN", "AC"),
        ("Railway-4.json", "UP", "AC")
    ]
    
    base_dir = Path(__file__).resolve().parent
    
    for filename, direction, t_type in files:
        filepath = base_dir / filename
        if not filepath.exists():
            filepath = Path(filename) # Fallback to working root
            
        print(f"Processing {filename}...")
        if not filepath.exists():
            print(f"  ❌ Could not find {filename}")
            continue

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"  ❌ Could not load {filename}: {e}")
            continue
            
        trains_list = data.get('trains', [])
        line_enum = getattr(LineType, "DOWN", LineType.UP) if direction == "DN" else LineType.UP
        priority_val = 1 if t_type == "AC" else 2
        
        for tr in trains_list:
            if 'schedule' in tr:
                times_dict = tr['schedule']
            elif 'times' in tr:
                times_dict = tr['times']
            else:
                continue
                
            stations = []
            for st, t in times_dict.items():
                if isinstance(t, str) and ":" in t and len(t.split(':')) == 2:
                    try:
                        h, m = map(int, t.split(':'))
                        stations.append({"station": st.strip(), "hour": h, "minute": m})
                    except ValueError:
                        pass
                        
            if len(stations) < 2:
                continue
                
            t_id = tr.get('train_no', 'UNK')
            current_date = BASE_DATE
            prev_dt = None
            
            for i in range(len(stations) - 1):
                st1_name = stations[i]['station']
                h1, m1 = stations[i]['hour'], stations[i]['minute']
                
                st2_name = stations[i+1]['station']
                h2, m2 = stations[i+1]['hour'], stations[i+1]['minute']
                
                entry_dt = current_date.replace(hour=h1, minute=m1, second=0, microsecond=0)
                if prev_dt and entry_dt < prev_dt:
                    current_date += timedelta(days=1)
                    entry_dt = current_date.replace(hour=h1, minute=m1, second=0, microsecond=0)
                    
                exit_dt = current_date.replace(hour=h2, minute=m2, second=0, microsecond=0)
                if exit_dt < entry_dt:
                    current_date += timedelta(days=1)
                    exit_dt = current_date.replace(hour=h2, minute=m2, second=0, microsecond=0)
                    
                # Enforce strict chronology (minimum 1-minute runtime)
                if exit_dt <= entry_dt:
                    exit_dt = entry_dt + timedelta(minutes=1)
                    
                prev_dt = exit_dt
                
                section_key = (st1_name, st2_name, line_enum)
                if section_key not in section_map:
                    end_chainage = current_chainage + 2.5
                    new_section = TrackSection(
                        section_name=f"{st1_name}-{st2_name}",
                        start_station_code=st1_name,
                        end_station_code=st2_name,
                        line_type=line_enum,
                        start_km=current_chainage,
                        end_km=end_chainage,
                        max_permissible_speed=100
                    )
                    db.add(new_section)
                    db.flush()
                    section_map[section_key] = new_section.id
                    current_chainage = end_chainage
                
                section_id = section_map[section_key]
                
                new_schedule = TrainSchedule(
                    train_number=str(t_id),
                    train_name=f"{direction} {t_type} {t_id}",
                    priority_level=priority_val,
                    track_section_id=section_id,
                    scheduled_entry=entry_dt,
                    scheduled_exit=exit_dt,
                    direction=line_enum
                )
                db.add(new_schedule)
                schedule_count += 1
                
    db.commit()
    print(f"\n✅ Successfully generated {len(section_map)} granular TrackSections.")
    print(f"✅ Successfully ingested {schedule_count} TrainSchedule block movements.")
    db.close()

if __name__ == '__main__':
    ingest_western_railway()