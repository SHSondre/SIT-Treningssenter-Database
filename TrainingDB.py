import sqlite3
from datetime import datetime, timedelta

ISOFMT = "%Y-%m-%d %H:%M:%S"
NOW = "2026-03-15 19:00:00"

def init():
    try:
        with open("init.sql", 'r', encoding='utf-8') as sqlfile:
            sqlscript = sqlfile.read()
        con = sqlite3.connect("TrainingDB.db")
        cursor = con.cursor()
        cursor.executescript(sqlscript)
        con.commit()
        print("DB initialized")
    except Exception as e:
        con.rollback()
        print(e)
    finally:
        con.close()

def book_training(user_email, activity_name, start_time, center_name):
    con = sqlite3.connect("TrainingDB.db")
    con.row_factory = sqlite3.Row
    try:
        now = NOW
        now_dt = datetime.strptime(now, ISOFMT)
        if now_dt > (datetime.strptime(start_time, ISOFMT) - timedelta(minutes=5)):
            raise ValueError("Can not book old sessions")

        cursor = con.cursor()

        cursor.execute("""
        SELECT s.session_id, r.capacity, s.start_time, s.end_time,
            (SELECT COUNT(*) FROM Booking b WHERE b.session_id = s.session_id AND b.status IN ('booked','checked_in')) AS booked_count
        FROM TrainingSession s
        JOIN Activity a ON s.activity_id = a.activity_id
        JOIN Room r ON s.room_id = r.room_id
        JOIN Center c ON r.center_id = c.center_id
        WHERE a.name = ? AND s.start_time = ? AND c.name = ?
        """, (activity_name, start_time, center_name))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Session not found")
                
        session_id = row["session_id"]
        capacity = row["capacity"]
        booked_count = int(row["booked_count"] or 0)
        session_start = row["start_time"]
        session_end = row["end_time"]
        
        cursor.execute("SELECT banned_until FROM SITUser WHERE email = ?", (user_email,))
        user = cursor.fetchone()
        if not user:
            raise ValueError("User not found")
        banned_until = user["banned_until"]
        if banned_until:
            banned_dt = datetime.strptime(banned_until, ISOFMT)
            if banned_dt > now_dt:
                raise ValueError(f"User is banned until {banned_until}")
            
        # avoid double-book of same session.
        cursor.execute("SELECT booking_id FROM Booking WHERE session_id = ? AND email = ? AND status != 'cancelled'", (session_id, user_email))
        double_book = cursor.fetchone()
        if double_book:
            raise ValueError("User already booked for this session")
        
        # avoid different session in same time window
        cursor.execute("""
        SELECT s.session_id, a.name, s.start_time, s.end_time
        FROM Booking b
        JOIN TrainingSession s ON b.session_id = s.session_id
        JOIN Activity a ON s.activity_id = a.activity_id
        WHERE b.email = ? AND b.status != 'cancelled' AND s.start_time < ? AND s.end_time > ?
        """, (user_email, session_end, session_start))
        overlap = cursor.fetchone()
        if overlap:
            raise ValueError(f"Time conflict with {overlap['name']} ({overlap['start_time']} to {overlap['end_time']})")
        
        if booked_count < capacity:
            status = "booked" 
        else: 
            status = "waitlist"
        cursor.execute("INSERT INTO Booking(session_id, email, booking_time, status) VALUES (?, ?, ?, ?)", 
                       (session_id, user_email, now, status))
        con.commit()
        print(f"Booked session {session_id} for {user_email}")
        return True
    except Exception as e:
        con.rollback()
        print("Booking failed:", e)
        return False
    finally:
        con.close()

def cancel_booking(user_email, activity_name, start_time, center_name):
    con = sqlite3.connect("TrainingDB.db")
    con.row_factory = sqlite3.Row
    try:
        cursor = con.cursor()
        cursor.execute("""SELECT s.session_id, s.start_time
                       FROM TrainingSession s
                       JOIN Activity a ON s.activity_id = a.activity_id
                       JOIN Room r ON s.room_id = r.room_id
                       JOIN Center c ON r.center_id = c.center_id
                       WHERE a.name = ? AND s.start_time = ? AND c.name = ?
                       """, (activity_name, start_time, center_name))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Session not found")
        session_id = row["session_id"]
        session_start = datetime.strptime(row["start_time"], ISOFMT)

        cursor.execute("SELECT booking_id, status FROM Booking WHERE session_id = ? AND email = ?", (session_id, user_email))
        b = cursor.fetchone()
        if not b:
            raise ValueError("No booking found for this user and session")
        booking_id = b["booking_id"]
        old_status = b["status"]

        if old_status == "cancelled":
            print("Booking is already cancelled")
            return True

        now_str = NOW
        now_dt = datetime.strptime(NOW, ISOFMT)

        if session_start - now_dt < timedelta(hours=1):
            expires_at = (now_dt + timedelta(days=30)).strftime(ISOFMT)
            cursor.execute("INSERT INTO Penalty (booking_id, email, date_given, expires_at, reason) VALUES (?, ?, ?, ?, ?)",
                           (booking_id, user_email, now_str, expires_at, "Late cancellation"))
            print("Penalty recorded due to late cancellation")

        cursor.execute("UPDATE Booking SET status = 'cancelled', cancelled_time = ? WHERE booking_id = ?",
                       (now_str, booking_id))
        con.commit()

        try:
            update_waitlist(activity_name, start_time, center_name)
        except Exception:
            pass    

        try:
            blacklisted = blacklist(user_email)
            if blacklisted:
                print(f"User {user_email} has been blacklisted due to penalty count")
        except Exception:
            pass

        print(f"Booking {booking_id} cancelled for {user_email}")
        return True
    except Exception as e:
        con.rollback()
        print("Cancellation failed:", e)
        return False
    finally:
        con.close()

def update_waitlist(activity_name, start_time, center_name):
    con = sqlite3.connect("TrainingDB.db")
    con.row_factory = sqlite3.Row
    try:
        cursor = con.cursor()
        cursor.execute("""
        SELECT s.session_id AS session_id, r.capacity AS capacity,
            (SELECT COUNT(*) FROM Booking b WHERE b.session_id = s.session_id AND b.status IN ('booked','checked_in')) AS booked_count
        FROM TrainingSession s
        JOIN Activity a ON s.activity_id = a.activity_id
        JOIN Room r ON s.room_id = r.room_id
        JOIN Center c ON r.center_id = c.center_id
        WHERE a.name = ? AND s.start_time = ? AND c.name = ?
        """, (activity_name, start_time, center_name))
        row = cursor.fetchone()
        if row is None:
            raise ValueError("No such session")
        session_id = row["session_id"]
        capacity = row["capacity"]
        booked_count = (row["booked_count"] or 0)
        open_spots = capacity - booked_count
        if open_spots <= 0:
            return False

        cursor.execute("""SELECT booking_id, email
                       FROM Booking
                       WHERE session_id = ? AND status = 'waitlist'
                       ORDER BY booking_time ASC
                       LIMIT ?""", (session_id, open_spots))
        rows = cursor.fetchall()
        if not rows:
            return False
        for row in rows:
            booking_id = row["booking_id"]
            cursor.execute("""UPDATE Booking SET status = 'booked' WHERE booking_id = ?""", (booking_id,))
        con.commit()
        return True
    except Exception as e:
        con.rollback()
        print(e)
        return False
    finally:
        con.close()

def register_attendance(user_email, activity_name, start_time, center_name):
    now_str = "2026-03-16 18:20:00"
    now_dt = datetime.strptime(now_str, ISOFMT)
    con = sqlite3.connect("TrainingDB.db")
    con.row_factory = sqlite3.Row
    try:
        cursor = con.cursor()
        cursor.execute("""
        SELECT b.booking_id, b.status, s.session_id
        FROM Booking b
        JOIN TrainingSession s ON b.session_id = s.session_id
        JOIN Activity a ON s.activity_id = a.activity_id
        JOIN Room r ON s.room_id = r.room_id
        JOIN Center c ON r.center_id = c.center_id
        WHERE a.name = ? AND b.email = ? AND s.start_time = ? AND c.name = ?
        """, (activity_name, user_email, start_time, center_name))        
        booking = cursor.fetchone()
        if not booking:
            raise ValueError("No booking found for user and session")
        booking_id = booking["booking_id"]
        status = booking["status"]
        session_id = booking["session_id"]
        start_time = datetime.strptime(start_time, ISOFMT)

        if now_dt > (start_time - timedelta(minutes=5)):
            now_str = NOW
            expires_at = (now_dt + timedelta(days=30)).strftime(ISOFMT)
            cursor.execute("INSERT INTO Penalty (booking_id, email, date_given, expires_at, reason) VALUES (?, ?, ?, ?, ?)",
               (booking_id, user_email, now_str, expires_at, "Late attendance"))
            print("Penalty recorded due to late attendance")
        if status != "booked":
            raise ValueError(f"Cannot check in when user-booking is {status}")
        
        cursor.execute("UPDATE Booking SET status = 'checked_in', showed_up_time = ? WHERE booking_id = ?", (now_str, booking_id))
        con.commit()
        print(f"User {user_email} checked in for session {session_id}")
        return True
    except Exception as e:
        con.rollback()
        print("Registration failed:", e)
        return False
    finally:
        con.close()

def week_plan(start_date):
    con = sqlite3.connect("TrainingDB.db")
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        week = start.isocalendar().week
        end = start + timedelta(days=7)
        cursor = con.cursor()
        cursor.execute(""" 
            SELECT s.session_id, a.name, c.name, r.name, s.start_time, s.end_time, i.first_name
            FROM TrainingSession s
            JOIN Activity a ON s.activity_id = a.activity_id
            JOIN Room r ON s.room_id = r.room_id
            JOIN Center c ON r.center_id = c.center_id
            JOIN Instructor i ON s.instructor_id = i.instructor_id
            WHERE s.start_time >= ? AND s.start_time < ?
            ORDER BY s.start_time ASC
        """, (start.strftime(ISOFMT), end.strftime(ISOFMT)))
        rows = cursor.fetchall()
        print(f'Showing plan for week {week} ({start_date} - {end.strftime("%Y-%m-%d")}):')
        print("session_id | activity | center | room | start time | end time | instructor")
        for r in rows: 
            print(r)
        return True
    except Exception as e:
        print("Could not fetch week plan:", e)
        return False
    finally:
        con.close()

def user_history(user_email, since):
    con = sqlite3.connect("TrainingDB.db")
    print(f"User history for {user_email} since {since}:")
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT DISTINCT a.name, c.name, s.start_time, s.end_time
            FROM Booking b
            JOIN TrainingSession s ON b.session_id = s.session_id
            JOIN Activity a ON s.activity_id = a.activity_id
            JOIN Room r ON s.room_id = r.room_id
            JOIN Center c ON r.center_id = c.center_id
            WHERE b.email = ? AND b.status = 'checked_in' AND s.start_time >= ?
            ORDER BY s.start_time ASC
        """, (user_email, since))   
        rows = cursor.fetchall()
        for r in rows: 
            print(r)
        return True
    except Exception as e:
        print("Could not fetch user history:", e)
        return False
    finally:
        con.close()

def check_attendance(user_email):
    con = sqlite3.connect("TrainingDB.db")
    con.row_factory = sqlite3.Row
    try:
        now_str = NOW
        now_dt = datetime.strptime(NOW, ISOFMT)
        cursor = con.cursor()
        cursor.execute("""SELECT b.booking_id, s.start_time
                       FROM Booking b 
                       JOIN TrainingSession s ON b.session_id = s.session_id
                       WHERE b.status = 'booked' AND b.showed_up_time is NULL AND b.email = ? AND s.start_time < ?
                       """, (user_email, now_str))
        rows = cursor.fetchall()
        for row in rows:
            booking_id = row["booking_id"]
            start_time = row["start_time"]
            expires_at = (datetime.strptime(start_time, ISOFMT) + timedelta(days=30))
            cursor.execute("""INSERT INTO Penalty(booking_id, email, date_given, expires_at, reason)
                           VALUES (?, ?, ?, ?, 'No-show')
                           """, (booking_id, user_email, start_time, expires_at.strftime(ISOFMT)))
            cursor.execute("UPDATE Booking SET status = 'no_show' WHERE booking_id = ?", (booking_id,))
            print(f"Penalty given to {user_email} until: {expires_at}")
        con.commit()
    except Exception as e:
        return False
    finally:
        con.close()

def blacklist(user_email):
    con = sqlite3.connect("TrainingDB.db")
    con.row_factory = sqlite3.Row
    try:
        now = datetime.strptime(NOW, ISOFMT)
        cutoff = (now - timedelta(days=30)).strftime(ISOFMT)
        cursor = con.cursor()
        cursor.execute("""SELECT COUNT(*) AS cnt, MIN(p.date_given) AS earliest
                       FROM Penalty p 
                       JOIN Booking b ON b.booking_id = p.booking_id
                       WHERE b.email = ? AND datetime(p.date_given) >= datetime(?)""", 
                       (user_email, cutoff))
        row = cursor.fetchone()
        count = int(row["cnt"] or 0)
        if count >= 3:
            earliest = datetime.strptime(row["earliest"], ISOFMT)
            banned_until = (earliest + timedelta(days=30)).strftime(ISOFMT)
            cursor.execute("UPDATE SITUser SET banned_until = ? WHERE email = ?", (banned_until, user_email))
            con.commit()
            print(f"User has been banned until: {banned_until}")
            return True
        else:
            print("User is not banned")
            return False
    except Exception as e:
        con.rollback()
        return False
    finally:
        con.close()

def top_attendees(year_month):
    """
    year_month: 'YYYY-MM' (e.g. '2026-01')
    Prints users with most check-ins that month.
    """
    con = sqlite3.connect("TrainingDB.db")
    con.row_factory = sqlite3.Row
    try:
        cursor = con.cursor()
        cursor.execute("""WITH counts AS (
                        SELECT b.email, COUNT(*) AS cnt
                       FROM Booking b JOIN TrainingSession s ON b.session_id = s.session_id
                       WHERE b.status = 'checked_in' AND substr(s.start_time,1,7) = ?
                       GROUP BY b.email)
                       SELECT email, cnt FROM counts WHERE cnt = (SELECT MAX(cnt) FROM counts)""", (year_month,))
        rows = cursor.fetchall()
        print("Top user(s):")
        for r in rows: 
            user_email = r["email"]
            count = r["cnt"]
            print(f"User {user_email} has trained {count} times!")
    finally:
        con.close()

def training_together():
    """
    Find pairs of users who checked in together, aggregated without duplicates (A,B only once).
    """
    con = sqlite3.connect("TrainingDB.db")
    con.row_factory = sqlite3.Row
    cursor = con.cursor()
    cursor.execute("""SELECT b1.email AS user_a, b2.email AS user_b, COUNT(*) AS shared_sessions
                   FROM Booking b1
                   JOIN Booking b2 ON b1.session_id = b2.session_id
                   WHERE b1.email < b2.email
                    AND b1.status = 'checked_in' AND b2.status = 'checked_in'
                   GROUP BY b1.email, b2.email
                   ORDER BY shared_sessions DESC""")
    rows = cursor.fetchall()
    #Can also be fetchone if we only want two pairs. Here we iterate over all pairs with the same maximum shared sessions
    for r in rows: 
        user_a = r["user_a"]
        user_b = r["user_b"]
        shared = r["shared_sessions"]
        print(f"{user_a} and {user_b} has shared {shared} sessions")
    con.close()

DESC = """
Training Database CLI:
* init (Use case 1)
* book_training (Use case 2)
* register_attendance (Use case 3)
* week_plan (Use case 4)
* user_history (Use case 5)
* blacklist (Use case 6)
* top_attendees (Use case 7)
* training_together (Use case 8)
type 'exit' to quit or 'help' for description
or type 1, 2, ..., 8 for quick use cases
"""
def main():
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(DESC)
    text = None
    while text != "exit":
        text = input(">")
        if text == "init" or text == "1":
            init()
        elif text == "help" or text == "?":
            print(DESC)
        elif text == "book_training" or text == "2":
            book_training("johnny@stud.ntnu.no", "Spin60", "2026-03-17 18:30:00", "Øya treningssenter")
        elif text == "register_attendance" or text == "3":
            register_attendance("johnny@stud.ntnu.no", "Spin60", "2026-03-17 18:30:00", "Øya treningssenter")
        elif text == "cancel_booking":
            cancel_booking("johnny@stud.ntnu.no", "Spin60", "2026-03-17 18:30:00", "Øya treningssenter")
        elif text == "week_plan" or text == "4":
            week_plan("2026-03-16")
        elif text == "user_history" or text == "5":
            user_history("johnny@stud.ntnu.no", "2026-01-01 00:00:00")
        elif text == "blacklist" or text == "6":
            check_attendance("johnny@stud.ntnu.no")
            blacklist("johnny@stud.ntnu.no")
        elif text == "top_attendees" or text == "7":
            top_attendees("2026-01")
        elif text == "training_together" or text == "8":
            training_together()
    return

if __name__ == "__main__":
    main()