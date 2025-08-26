const container = document.getElementById("weekly-cal");
const prevButton = document.getElementById("prevWeek");
const nextButton = document.getElementById("nextWeek");
const weekLabel = document.getElementById("current-week");

let current_week_first;
let current_week_last;
let currentWeek = 0;

function getWeek(current_week) {
  const grouped = {};
  container.innerHTML = "";
  fetch(`/data?week=${current_week}`)
    .then((res) => res.json())
    .then((data) => {
      data = Object.entries(data).map(([key, value]) => {
        return { slot_id: Number(key), ...value };
      });
      current_week_first = new Date(data[0].time).toLocaleDateString("en-us", {
        month: "short",
        day: "numeric",
      });
      current_week_last = new Date(
        data[data.length - 1].time
      ).toLocaleDateString("en-us", { month: "short", day: "numeric" });

      weekLabel.textContent = current_week_first + " - " + current_week_last;

      data.forEach((item) => {
        const obj = new Date(item.time);
        const date = obj.toLocaleDateString("en-us", {
          weekday: "short",
          month: "short",
          day: "numeric",
        });
        const time = obj.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });
        if (!grouped[date]) {
          grouped[date] = [];
        }
        grouped[date].push({
          time: time,
          slot_id: item.slot_id,
          available: item.available,
        });
      });
    })
    .then(() => {
      for (const [date, times] of Object.entries(grouped)) {
        const section = document.createElement("div");

        const title = document.createElement("h3");
        title.textContent = date;
        section.appendChild(title);

        const ul = document.createElement("ul");
        ul.classList.add("schedule");
        times.forEach((slot) => {
          const li = document.createElement("li");
          li.textContent = slot.time;
          li.classList.add("slot");
          li.id = `slot-${slot.slot_id}`;
          if (!slot.available) li.classList.add("unavailable");
          ul.appendChild(li);
        });

        section.appendChild(ul);
        container.appendChild(section);
      }
    })
    .then(() => {
      const lists = document.querySelectorAll(".schedule");

      lists.forEach((list) => {
        list.addEventListener("click", function (e) {
          if (e.target && e.target.nodeName === "LI") {
            const classes = e.target.classList;
            if (classes.contains("unavailable")) {
              const data = { id: e.target.id, status: "True" };
              fetch("/data/time-slot", {
                method: "POST", // specify POST
                headers: {
                  "Content-Type": "application/json", // sending JSON
                },
                body: JSON.stringify(data), // convert JS object to JSON string
              });
            } else {
              const data = { id: e.target.id, status: "False" };
              fetch("/data/time-slot", {
                method: "POST", // specify POST
                headers: {
                  "Content-Type": "application/json", // sending JSON
                },
                body: JSON.stringify(data), // convert JS object to JSON string
              });
            }
            e.target.classList.toggle("unavailable");
          }
        });
      });
    });
  console.log(currentWeek);
  if (currentWeek < 3) {
    nextButton.classList.add("show");
  } else {
    nextButton.classList.remove("show");
  }
  if (currentWeek > 0) {
    prevButton.classList.add("show");
  } else {
    prevButton.classList.remove("show");
  }
}

getWeek(currentWeek);

// Button handlers
document.getElementById("prevWeek").addEventListener("click", () => {
  currentWeek--;
  getWeek(currentWeek);
});

document.getElementById("nextWeek").addEventListener("click", () => {
  currentWeek++;
  getWeek(currentWeek);
});
