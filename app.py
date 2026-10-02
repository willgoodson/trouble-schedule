from flask import Flask, request, render_template, g
import datetime as dt
import os
import sqlite3
import time
import threading

DATABASE = 'scheduler.db'

app = Flask(__name__)

def get_db():
    '''Returns Database'''
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    '''Initializes Database Tables'''
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS time_slots (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            time      TEXT NOT NULL,
            ordinal   INTEGER NOT NULL,
            available INTEGER NOT NULL,
            UNIQUE(time, ordinal)
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weekday INTEGER NOT NULL,
            ordinals INTEGER NOT NULL,
            start TEXT NOT NULL,
            end TEXT,
            UNIQUE(weekday, start, end)
        )
    """)
    db.commit()

def refresh_schedule(date=dt.datetime.today()):
    db = get_db()
    today = dt.date.today()
    this_week_start = today - dt.timedelta(days=today.weekday())
    db.execute("""
               DELETE FROM schedules WHERE end < ?;
               """, (dt.datetime.today().strftime("%Y-%m-%d"),))
    db.execute("""
               DELETE FROM time_slots WHERE time > ?;
               """, (date.strftime("%Y-%m-%d %H:%M:%S"),))
    db.execute("""
               DELETE FROM time_slots WHERE time < ?;
               """, (this_week_start.isoformat(),))
    db.commit()

    for offset in range(28):
        day = this_week_start + dt.timedelta(days=offset)
        weekday = day.weekday()

        # Pull schedules for this weekday
        rows = db.execute("""
            SELECT ordinals, start, end
            FROM schedules
            WHERE weekday = ?
            AND date(?) BETWEEN date(start) AND date(COALESCE(end, ?))
        """, (weekday, day.isoformat(), day.isoformat())).fetchall()

        # Loop Over Schedules and Create and Insert Time Slots into Database
        for row in rows:
            capacity, start_str, end_str = row
            start_time = dt.datetime.combine(day, dt.datetime.fromisoformat(start_str).time())
            for ordinal in range(capacity):
                db.execute("""
                    INSERT OR IGNORE INTO time_slots (time, ordinal, available)
                    VALUES (?, ?, 1)
                """, (start_time.isoformat(), ordinal))
    db.commit()


def schedule_refresh():
    '''Checks if it is currently the start of the week every 8 hours (3 times a day) and refreshes schedule if it is the start of the week.'''
    with app.app_context():
        refresh_schedule(dt.datetime.today())
        while True:
            day = dt.datetime.today().weekday()

            if day == 0:
                refresh_schedule(dt.datetime.today())

            time.sleep(28800)

@app.route('/')
def default():
    '''Default Root. Renders the HTML Template.'''
    return render_template('index.html'), 200

@app.route('/admin', methods=['GET', 'POST'])
def admin_dash():
    '''Admin Route. Renders HTML for Admin Dashboard.'''
    if request.method == 'GET':
        return render_template('admin.html'), 200
    elif request.method == 'POST':
        db = get_db()
        eff_date = dt.datetime.strptime(request.get_json()['effective_date'], "%Y-%m-%d")
        db.execute("""
                    UPDATE schedules
                    SET end = ?
                    WHERE end IS NULL;
                   """, (eff_date.strftime("%Y-%m-%d %H:%M:%S"),))
        for slot in request.get_json()['slots']:
            db.execute("""
                       INSERT INTO schedules (weekday, ordinals, start)
                       VALUES (?, ?, ?);
                       """, (slot['weekday'], slot['capacity'], (eff_date + dt.timedelta(hours=slot['hour'])).strftime("%Y-%m-%d %H:%M:%S")))
        db.commit()
        refresh_schedule(eff_date)

        return ('okay', 201)

@app.route('/data')
def data():
    '''Data Route. Fetch Data for Target Week.'''
    # Get offset from request. Default to current week.
    week_offset = int(request.args.get('week', 0))

    # Get Current Week Start and Apply Offset to Calculate Target Week
    today = dt.date.today()
    this_week_start = today - dt.timedelta(days=today.weekday())
    target_start = this_week_start + dt.timedelta(weeks=week_offset)
    target_end = target_start + dt.timedelta(days=6)

    # Open Database and Fetch Time Slots in Target Week.
    db = get_db()
    rows = db.execute("""
        SELECT * FROM time_slots
        WHERE time BETWEEN ? AND ?
        ORDER BY time, ordinal
    """, (target_start.isoformat(), target_end.isoformat())).fetchall()

    # Format and Return Data
    result = {
        row['id']: {
            'time': row['time'],
            'ordinal': row['ordinal'],
            'available': bool(row['available'])
        }
        for row in rows
    }
    return result

@app.route('/data/time-slot', methods=['POST'])
def update_time_slot():
    '''Data Route. Update Time Slot Availability.'''
    # Get ID from Request Body and Reformat It
    data = request.get_json()
    id = int(data.get('id').split('-')[1])
    status = data.get('status')

    # Attempt to Update Status
    if (status == 'False'):
        db = get_db()
        db.execute("""
                   UPDATE time_slots
                   SET available = 0
                   WHERE id = ?;
                   """, (id,))
        db.commit()
        return f'Set ID: {id} To Unavailable.', 201
    elif (status == 'True'):
        db = get_db()
        db.execute("""
                   UPDATE time_slots
                   SET available = 1
                   WHERE id = ?;
                   """, (id,))
        db.commit()
        return f'Set ID: {id} To Available.', 201
    else:
        return f'Invalid Status! ID: {id} Unchanged.', 400

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    '''Application Entry Point'''
    with app.app_context():
        init_db()
    refresh_thread = threading.Thread(target=schedule_refresh, daemon=True)
    refresh_thread.start()
    app.run(port=8000, debug=os.environ.get('FLASK_DEBUG') == '1')