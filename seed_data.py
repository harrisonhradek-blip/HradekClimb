# NOTE this is AI

"""
Seeds climbing.db with sample data for a 'test' user so the dashboard
(homepage charts, monthly bests, session list) has something to show.

Usage:
    python3 seed_data.py

Run this from inside your project folder (where climbing.db lives), or
edit DB_PATH below to point at it.
"""

import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "climbing.db"

USERNAME = "test"
PASSWORD_HASH = "scrypt:32768:8:1$voqRv8acoUmRU0vo$86a65a285fce62ed5fcaf848d02d708e9b3b2002897b085f5d83bba12cdc76a71b870d400a6d4ba350d4e49e0270b235422df4951a50fc2e6a2c591347840835"

random.seed(42)  # deterministic output, delete this line if you want fresh random data each run

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # 1. Create (or reuse) the test user
    cur.execute("SELECT id FROM users WHERE username = ?", (USERNAME,))
    row = cur.fetchone()
    if row:
        user_id = row[0]
        print(f"User '{USERNAME}' already exists (id={user_id}), reusing it.")
    else:
        cur.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            (USERNAME, PASSWORD_HASH),
        )
        user_id = cur.lastrowid
        print(f"Created user '{USERNAME}' (id={user_id}).")

    # 2. Build 6 months of sessions, with grades trending upward over time
    #    so the "hardest grade per month" list and the volume chart both
    #    show a believable progression.
    today = datetime.now()
    months_back = 6
    base_grade = 2  # starts around V2

    total_sessions = 0
    total_climbs = 0

    for m in range(months_back, 0, -1):
        month_date = today - timedelta(days=30 * m)
        # 2-4 sessions per month
        sessions_this_month = random.randint(2, 4)
        # grade ceiling creeps up ~1 grade every couple months
        month_max_grade = base_grade + (months_back - m) // 2

        for _ in range(sessions_this_month):
            # random day within that month
            day_offset = random.randint(0, 27)
            session_date = (month_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")

            cur.execute(
                "INSERT INTO user_sessions (user_id, date) VALUES (?, ?)",
                (user_id, session_date),
            )
            session_id = cur.lastrowid
            total_sessions += 1

            # 3-6 climbs per session
            num_climbs = random.randint(3, 6)
            for _ in range(num_climbs):
                hours = round(random.uniform(0.5, 2.5), 1)
                cur.execute(
                    "INSERT INTO session_climbs (session_id, hours) VALUES (?, ?)",
                    (session_id, hours),
                )
                climb_id = cur.lastrowid

                # grade somewhere between V0 and this month's max (occasionally +1 for a "project")
                grade_numeric = max(0, random.randint(month_max_grade - 3, month_max_grade))
                if random.random() < 0.15:
                    grade_numeric = month_max_grade + 1  # attempted project, often unsent
                grade = f"V{grade_numeric}"

                # harder climbs sent less often
                send_chance = max(0.25, 0.9 - (grade_numeric / 12))
                sent = 1 if random.random() < send_chance else 0
                attempts = random.randint(1, 3) if sent else random.randint(2, 8)

                cur.execute(
                    """INSERT INTO climb_data
                       (climb_id, grade, grade_numeric, sent, attempts)
                       VALUES (?, ?, ?, ?, ?)""",
                    (climb_id, grade, grade_numeric, sent, attempts),
                )
                total_climbs += 1

    conn.commit()
    conn.close()
    print(f"Inserted {total_sessions} sessions and {total_climbs} climbs for '{USERNAME}'.")
    print("Log in with username 'test' and the password that matches the given hash.")


if __name__ == "__main__":
    main()