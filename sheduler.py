import os
import subprocess
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from datetime import datetime

# Vietnam timezone
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')

def run_sync():
    """Run sync script"""
    print(f"\n{'='*60}")
    print(f"⏰ Starting sync at {datetime.now(vn_tz).strftime('%Y-%m-%d %H:%M:%S')} VN time")
    print(f"{'='*60}\n")
    
    # Run test.py
    result = subprocess.run(
        ['python', 'test.py'],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(__file__)
    )
    
    print(result.stdout)
    if result.stderr:
        print("ERRORS:", result.stderr)
    
    print(f"\n✅ Sync completed!")

# Create scheduler
scheduler = BlockingScheduler(timezone=vn_tz)

# Schedule at 9AM VN time every day
scheduler.add_job(
    run_sync,
    trigger=CronTrigger(hour=9, minute=0),  # 9:00 AM
    id='client_sync_9am',
    name='Daily Client Sync at 9AM',
    replace_existing=True
)

print("🚀 Scheduler started!")
print("📅 Script sẽ chạy lúc 9:00 AM VN time mỗi ngày")
print("⏸️  Press Ctrl+C to stop\n")

try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    print("\n⏹️  Scheduler stopped")