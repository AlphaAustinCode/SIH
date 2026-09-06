import json
import os
from datetime import datetime, timedelta

from app.database.session import SessionLocal
from app.database.models import (
    TrackSection, 
    TrainSchedule, 
    LineType, 
    AllocatedBlock, 
    MaintenanceRequest
)

def parse_time(time_str: str, base_date: datetime, previous_time: datetime = None) -> datetime:
    """Parses 'HH:MM' string to datetime, handling rollovers and repairing dirty data."""
    if not time_str:
        return None
        
    hours, minutes = map(int, time_str.split(':'))
    current_time = base_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    
    if previous_time:
        # 1. Genuine Midnight Rollover: Previous is late night, Current is early morning
        if previous_time.hour >= 20 and current_time.hour <= 4:
            current_time += timedelta(days=1)
            
        # 2. Repair Dirty Data / Typos: 
        # If current_time is STILL <= previous_time, it is a typo or a same-minute log.
        # We enforce chronological order by assuming a minimum 2-minute transit time.
        if current_time <= previous_time:
            current_time = previous_time + timedelta(minutes=2)
            
    return current_time

def ingest_real_schedule(json_filepath: str):
    db = SessionLocal()
    
    print("Clearing old data in correct foreign-key order...")
    db.query(MaintenanceRequest).delete()
    db.query(AllocatedBlock).delete()
    db.query(TrainSchedule).delete()
    db.query(TrackSection).delete()
    db.commit()

    print(f"Loading data from {json_filepath}...")
    if not os.path.exists(json_filepath):
        print(f"Error: Could not find {json_filepath}")
        return

    with open(json_filepath, 'r') as f:
        train_data = json.load(f)

    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    section_map = {}
    current_chainage = 0.0
    schedule_count = 0

    for train in train_data:
        t_id = train.get('train_id')
        stations = train.get('stations', [])
        line = LineType.UP  # Using your project's LineType enum
        
        prev_time = None
        
        for i in range(len(stations) - 1):
            st1_name = stations[i]['station']
            t1_str = stations[i]['time']
            
            st2_name = stations[i+1]['station']
            t2_str = stations[i+1]['time']
            
            entry_time = parse_time(t1_str, base_date, prev_time)
            exit_time = parse_time(t2_str, base_date, entry_time)
            prev_time = exit_time
            
            section_key = (st1_name, st2_name, line)
            if section_key not in section_map:
                end_chainage = current_chainage + 2.5
                
                new_section = TrackSection(
                    section_name=f"{st1_name}-{st2_name}",
                    start_station_code=st1_name,
                    end_station_code=st2_name,
                    line_type=line,
                    start_km=current_chainage,
                    end_km=end_chainage,
                    max_permissible_speed=110
                )
                db.add(new_section)
                db.flush() 
                
                section_map[section_key] = new_section.id
                current_chainage = end_chainage
            
            section_id = section_map[section_key]
            
            new_schedule = TrainSchedule(
                train_number=str(t_id),
                train_name=f"Local {t_id}",
                priority_level=2,  # Integer priority level
                track_section_id=section_id,
                scheduled_entry=entry_time,
                scheduled_exit=exit_time,
                direction=line
            )
            db.add(new_schedule)
            schedule_count += 1
            
    db.commit()
    print(f"Successfully generated {len(section_map)} granular TrackSections.")
    print(f"Successfully ingested {schedule_count} TrainSchedule block movements.")
    db.close()

if __name__ == "__main__":
    ingest_real_schedule("scripts/trains.json")