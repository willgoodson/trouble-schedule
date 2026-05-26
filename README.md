# Trouble Scheduler

## Overview
This project exists due to not being able to find anything similar. It is a basic time slot calendar that allows for multiple slots for the specified time periods. It displays in a weekly view and allows multiple weeks to be populated. You can modify schedules through the admin page. Modifying the schedule does not remove currently booked appointments. All data is stored in an sqlite database which is polled periodically to pull any updates. This allows it to be used by multiple concurrent users.

### Future Work
- Add a data field for comments on each time slot
- Redesign updating mechanism to be scalable for multiple users

## Application Stack

**Languages:** Python, SQL

**Database:** SQLite

**API Framework:** Flask
