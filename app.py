from flask import Flask, request, render_template, g
import datetime as dt
import sqlite3

AVAILABILITY = [
    #Monday
    [
        (dt.timedelta(hours=8), 1),
        (dt.timedelta(hours=10), 2),
        (dt.timedelta(hours=13), 3),
        (dt.timedelta(hours=15), 4)
    ],
    #Tuesday
    [
        (dt.timedelta(hours=8), 2),
        (dt.timedelta(hours=10), 3),
        (dt.timedelta(hours=13), 3),
        (dt.timedelta(hours=15), 4)
    ],
    #Wednesday
    [
        (dt.timedelta(hours=8), 2),
        (dt.timedelta(hours=10), 3),
        (dt.timedelta(hours=13), 3),
        (dt.timedelta(hours=15), 4)
    ],
    #Thursday
   [
        (dt.timedelta(hours=8), 2),
        (dt.timedelta(hours=10), 3),
        (dt.timedelta(hours=13), 3),
        (dt.timedelta(hours=15), 4)
    ],
    #Friday
    [
        (dt.timedelta(hours=8), 2),
        (dt.timedelta(hours=10), 3),
        (dt.timedelta(hours=13), 3),
        (dt.timedelta(hours=15), 4)
    ],
    #Saturday
    [
        (dt.timedelta(hours=8), 1),
        (dt.timedelta(hours=10), 1),
        (dt.timedelta(hours=13), 1),
        (dt.timedelta(hours=15), 1)
    ]
]

slot_id_count = 0
time_slots = {}
this_week = []

DATABASE = 'scheduler.db'


app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS time_slots (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            date      TEXT NOT NULL,
            time      TEXT NOT NULL,
            ordinal   INTEGER NOT NULL,
            available INTEGER NOT NULL,
            UNIQUE(date, time, ordinal)
        )
    """)
    db.commit()


def populate_dates(start_date, days=7):
    db = get_db()
    for offset in range(days):
        day = start_date + dt.timedelta(days=offset)
        weekday = day.weekday()

        if weekday >= len(AVAILABILITY):  # skip if outside config
            continue

        for time_delta, capacity in AVAILABILITY[weekday]:
            slot_date = day.isoformat()
            slot_time = day.replace(hour=0, minute=0, second=0) + time_delta

            for ordinal in range(capacity):
                db.execute("""
                    INSERT OR IGNORE INTO time_slots (date, time, ordinal, available)
                    VALUES (?, ?, ?, 1)
                """, (slot_date, slot_time, ordinal))
    db.commit()


@app.route('/')
def default():
    return render_template('index.html')

@app.route('/data')
def data():
    week_offset = int(request.args.get('week', 0))  # e.g. -1, 0, +1
    today = dt.date.today()
    this_week_start = today - dt.timedelta(days=today.weekday())
    target_start = this_week_start + dt.timedelta(weeks=week_offset)
    target_end = target_start + dt.timedelta(days=6)

    db = get_db()
    rows = db.execute("""
        SELECT * FROM time_slots
        WHERE date BETWEEN ? AND ?
        ORDER BY date, time, ordinal
    """, (target_start.isoformat(), target_end.isoformat())).fetchall()

    result = {
        row['id']: {
            'date': row['date'],
            'time': row['time'],
            'ordinal': row['ordinal'],
            'available': bool(row['available'])
        }
        for row in rows
    }
    return result

@app.route('/data/time-slot', methods=['POST'])
def update_time_slot():
    data = request.get_json()
    id = int(data.get('id').split('-')[1])
    if (data.get('status') == 'False'):
        db = get_db()
        db.execute("""
                   UPDATE time_slots
                   SET available = 0
                   WHERE id = ?;
                   """, (id,))
        db.commit()
        return f'good {data.get('id').split('-')[1]}'
    elif (data.get('status') == 'True'):
        db = get_db()
        db.execute("""
                   UPDATE time_slots
                   SET available = 1
                   WHERE id = ?;
                   """, (id,))
        db.commit()
        return f'good {data.get('id').split('-')[1]}'
    else:
        return "Bad Input"

if __name__ == '__main__':
    with app.app_context():
        init_db()
        db = get_db()
        if db.execute('SELECT COUNT(*) FROM time_slots').fetchone()[0] == 0:
            populate_dates(dt.datetime.today(), 28)
    app.run(port='8000', debug=True)