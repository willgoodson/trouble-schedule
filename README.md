# Trouble Scheduler

A simple weekly time-slot booking calendar. Each time period can hold several slots, so more than one person can book the same hour.

## Overview

I built this because I couldn't find anything similar. Bookings show up in a weekly calendar, and you can page up to three weeks ahead. An admin page lets you define the recurring weekly schedule (which hours are open on each weekday and how many slots each hour has) starting from an effective date. Changing the schedule doesn't remove appointments that are already booked.

Everything is stored in SQLite. The page polls the server every 5 seconds, so several people can use it at once and see each other's bookings.

## Features

- Weekly calendar view covering the current week and the next three
- Multiple bookable slots per time period
- Click a slot to toggle it between available and booked
- Admin schedule builder: per-weekday hours and capacity, with an effective date
- A background job keeps four weeks of time slots generated, refreshing at the start of each week
- Live-ish updates by polling every 5 seconds

## Tech Stack

| Layer    | Technology              |
|----------|-------------------------|
| Language | Python, SQL, JavaScript |
| Backend  | Flask                   |
| Database | SQLite                  |
| Frontend | HTML/CSS + vanilla JS   |

## Project Structure

```
app.py              Flask app: routes, schedule generation, background refresh thread
templates/
  index.html        Weekly calendar
  admin.html        Schedule builder
static/
  script.js         Calendar rendering, polling, slot toggling
  styles.css
```

## Getting Started

**Prerequisites:** Python 3.9+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

`scheduler.db` is created automatically on first run.

- Calendar: http://localhost:8000
- Admin: http://localhost:8000/admin

## API

| Method | Route             | Description                                                    |
|--------|-------------------|----------------------------------------------------------------|
| GET    | `/data?week=N`    | Time slots for the week N weeks from now (default: 0, this week) |
| POST   | `/data/time-slot` | Set a slot's availability: `{"id": "slot-<id>", "status": "True"\|"False"}` |
| POST   | `/admin`          | Replace the schedule: `{"effective_date": "YYYY-MM-DD", "slots": [{"weekday", "hour", "capacity"}]}` |

## Future Work

- [ ] **Add authentication to the admin page.** Right now anyone who can reach the app can change the schedule.
- [ ] Add a comments field to each time slot (for example, who booked it and why)
- [ ] Replace 5-second polling with server push (Server-Sent Events or WebSockets) so it scales to more users
- [ ] Prevent double-booking races: only mark a slot booked if it's still available
- [ ] Add a production config (turn off `debug=True`, serve with gunicorn, read settings from environment variables)
- [ ] Remove the unused `/api/test` route and fix the duplicated `UNIQUE(time, time, ordinal)` constraint
- [ ] Add tests for schedule generation (`refresh_schedule`)
- [ ] Add a Dockerfile for one-command deployment
