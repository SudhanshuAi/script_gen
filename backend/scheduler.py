import os
import json
import uuid
import threading
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).parent.resolve()
SCHEDULES_FILE = BACKEND_DIR / "schedules.json"

class DataScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.schedules: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self._load_schedules()
        self.scheduler.start()
        logger.info("DataScheduler initialized and started.")

    def _load_schedules(self):
        if SCHEDULES_FILE.exists():
            try:
                with open(SCHEDULES_FILE, "r") as f:
                    self.schedules = json.load(f)
                
                # Restart jobs
                for sid, sdata in self.schedules.items():
                    self._add_to_apscheduler(sid, sdata)
                logger.info(f"Loaded {len(self.schedules)} schedules from storage.")
            except Exception as e:
                logger.error(f"Failed to load schedules: {e}")

    def _save_schedules(self):
        try:
            with open(SCHEDULES_FILE, "w") as f:
                json.dump(self.schedules, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save schedules: {e}")

    def _add_to_apscheduler(self, schedule_id: str, sdata: Dict[str, Any]):
        interval_hours = sdata.get("interval_hours", 1)
        self.scheduler.add_job(
            func=self.execute_run,
            trigger=IntervalTrigger(hours=interval_hours),
            args=[schedule_id],
            id=schedule_id,
            replace_existing=True
        )

    def add_schedule(self, schema: Dict, connection_string: Optional[str], 
                    interval_hours: float, rows_per_run: int, 
                    base_job_id: str, temporal_mode: str = "fixed") -> Dict[str, Any]:
        schedule_id = str(uuid.uuid4())
        sdata = {
            "schedule_id": schedule_id,
            "schema": schema,
            "connection_string": connection_string,
            "interval_hours": interval_hours,
            "temporal_mode": temporal_mode,
            "rows_per_run": rows_per_run,
            "base_job_id": base_job_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_run_at": None,
            "last_run_status": "idle",
            "run_count": 0,
            "run_history": []
        }
        
        with self.lock:
            self.schedules[schedule_id] = sdata
            self._add_to_apscheduler(schedule_id, sdata)
            self._save_schedules()
            
        return sdata

    def remove_schedule(self, schedule_id: str):
        with self.lock:
            if schedule_id in self.schedules:
                try:
                    self.scheduler.remove_job(schedule_id)
                except:
                    pass
                del self.schedules[schedule_id]
                self._save_schedules()
                return True
        return False

    def get_all_schedules(self) -> List[Dict[str, Any]]:
        with self.lock:
            # Enrich with next run time from APScheduler
            results = []
            for sid, sdata in self.schedules.items():
                job = self.scheduler.get_job(sid)
                enriched = sdata.copy()
                enriched["next_run_at"] = job.next_run_time.isoformat() if job and job.next_run_time else None
                results.append(enriched)
            return results

    def trigger_now(self, schedule_id: str):
        if schedule_id in self.schedules:
            # Run in a separate thread to not block API
            threading.Thread(target=self.execute_run, args=[schedule_id, True]).start()
            return True
        return False

    def execute_run(self, schedule_id: str, manual: bool = False):
        sdata = self.schedules.get(schedule_id)
        if not sdata:
            return

        run_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        logger.info(f"Executing run {run_id} for schedule {schedule_id}")
        
        try:
            # Use job_manager to start the job
            from job_manager import run_job_sync, jobs
            
            # Setup a temporary job entry in job_manager to track this run if desired,
            # but here we'll just run it sync in this background thread.
            
            # We need to update sdata status
            with self.lock:
                sdata["last_run_status"] = "running"
                self._save_schedules()

            # Prepare job_id for job_manager
            jm_job_id = f"sched_{run_id}"
            jobs[jm_job_id] = {"status": "pending", "result": None, "error": None}
            
            # ── Dynamic Temporal Update ──────────────────────────────────
            local_schema = sdata["schema"].copy()
            if sdata.get("temporal_mode") == "rolling":
                now_dt = datetime.now(timezone.utc)
                window_start = now_dt - timedelta(hours=sdata["interval_hours"])
                if "temporal" not in local_schema:
                    local_schema["temporal"] = {}
                local_schema["temporal"]["start_date"] = window_start.strftime("%Y-%m-%d")
                local_schema["temporal"]["end_date"] = now_dt.strftime("%Y-%m-%d")
                logger.info(f"Rolling mode: Updated temporal range to {local_schema['temporal']['start_date']} to {local_schema['temporal']['end_date']}")

            run_job_sync(
                job_id=jm_job_id,
                schema=local_schema,
                connection_string=sdata["connection_string"],
                incremental=True,
                incremental_rows=sdata["rows_per_run"],
                base_job_id=sdata["base_job_id"]
            )
            
            res = jobs[jm_job_id]
            
            with self.lock:
                sdata["last_run_at"] = datetime.now(timezone.utc).isoformat()
                sdata["last_run_status"] = res["status"]
                sdata["run_count"] += 1
                
                history_entry = {
                    "run_id": run_id,
                    "timestamp": sdata["last_run_at"],
                    "status": res["status"],
                    "manual": manual,
                    "total_records": res.get("result", {}).get("total_records", 0) if res["status"] == "completed" else 0,
                    "error": res.get("error")
                }
                sdata["run_history"].insert(0, history_entry)
                sdata["run_history"] = sdata["run_history"][:20] # Keep last 20
                self._save_schedules()
                
            logger.info(f"Run {run_id} finished with status {res['status']}")
            
        except Exception as e:
            logger.error(f"Schedule run failed: {e}")
            with self.lock:
                sdata["last_run_status"] = "failed"
                history_entry = {
                    "run_id": run_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "failed",
                    "manual": manual,
                    "error": str(e)
                }
                sdata["run_history"].insert(0, history_entry)
                self._save_schedules()

# Global instance
data_scheduler = DataScheduler()
