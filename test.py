from schedulr.core import Database
import datetime

db = Database()

# Clear existing data first
db.cur.execute("DELETE FROM task")
db.conn.commit()

# Add some test data
test_tasks = [
    ("Morning Meeting", f"{datetime.date.today()} 09:00:00"),
    ("Lunch Break", f"{datetime.date.today()} 12:30:00"),
    ("Project Review", f"{datetime.date.today() + datetime.timedelta(days=1)} 14:00:00"),
    ("Team Standup", f"{datetime.date.today() + datetime.timedelta(days=2)} 10:00:00"),
    ("Client Call", f"{datetime.date.today() + datetime.timedelta(days=3)} 15:30:00"),
]

for title, date_time in test_tasks:
    db.create_task(title, date_time)

print("Test data added successfully!")
print(f"Total tasks: {len(db.get_all_tasks())}")