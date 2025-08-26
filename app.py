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
            UNIQUE(date, time, ordinal)
        )
    """)
    db.commit()


def populate_dates(start_date, days=7):
    '''Populate Table with Set Amount Days From Start Date. Default: 7'''
    # Open Database Connection
    db = get_db()
    # Create and Insert Time Slots for All Requested Days into Database
    for offset in range(days):
        # Get Day and Ensure it is Within Scheduled Availability
        day = start_date + dt.timedelta(days=offset)
        weekday = day.weekday()
        if weekday >= len(AVAILABILITY):
            continue
        # Loop Over Available Slots Per Time and Insert Slots into Table
        for time_delta, capacity in AVAILABILITY[weekday]:
            slot_time = day.replace(hour=0, minute=0, second=0) + time_delta
            for ordinal in range(capacity):
                db.execute("""
                    INSERT OR IGNORE INTO time_slots (time, ordinal, available)
                    VALUES (?, ?, 1)
                """, (slot_time, ordinal))
    db.commit()


@app.route('/')
def default():
    '''Default Root. Renders the HTML Template.'''
    return render_template('index.html'), 200

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
        print(exception)
        db.close()

if __name__ == '__main__':
    '''Application Entry Point'''
    with app.app_context():
        init_db()
        db = get_db()
        if db.execute('SELECT COUNT(*) FROM time_slots').fetchone()[0] == 0:
            populate_dates(dt.datetime.today(), 28)
    app.run(port='8000', debug=True)