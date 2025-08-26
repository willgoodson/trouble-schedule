const container = document.getElementById("weekly-cal");
const prevButton = document.getElementById("prevWeek");
const nextButton = document.getElementById("nextWeek");
const weekLabel = document.getElementById("current-week");
const themeToggle = document.getElementById("theme-toggle");
const body = document.body;

let currentWeek = 0;

// Fetch and render a week
async function getWeek(current_week) {
  const response = await fetch(`/data?week=${current_week}`);
  let data = await response.json();

  data = Object.entries(data).map(([key, value]) => ({
    slot_id: Number(key),
    ...value,
  }));
  if (!data.length) return;

  // Clear container if week changed
  const existingWeek = container.getAttribute("data-current-week");
  if (existingWeek != current_week) {
    container.innerHTML = "";
    container.setAttribute("data-current-week", current_week);
  }

  // Update week label
  const current_week_first = new Date(data[0].time).toLocaleDateString(
    "en-us",
    { month: "short", day: "numeric" }
  );
  const current_week_last = new Date(
    data[data.length - 1].time
  ).toLocaleDateString("en-us", { month: "short", day: "numeric" });
  weekLabel.textContent = `${current_week_first} - ${current_week_last}`;

  // Group by date
  const grouped = {};
  data.forEach((item) => {
    const date = new Date(item.time).toLocaleDateString("en-us", {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
    const time = new Date(item.time).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    if (!grouped[date]) grouped[date] = [];
    grouped[date].push({
      time,
      slot_id: item.slot_id,
      available: item.available,
    });
  });

  // Update DOM
  for (const [date, times] of Object.entries(grouped)) {
    let section = document.getElementById(`section-${date}`);
    if (!section) {
      section = document.createElement("div");
      section.id = `section-${date}`;

      const title = document.createElement("h3");
      title.textContent = date;
      section.appendChild(title);

      const ul = document.createElement("ul");
      ul.classList.add("schedule");
      section.appendChild(ul);

      container.appendChild(section);
    }

    const ul = section.querySelector("ul");
    times.forEach((slot) => {
      let li = document.getElementById(`slot-${slot.slot_id}`);
      if (!li) {
        li = document.createElement("li");
        li.textContent = slot.time;
        li.classList.add("slot");
        li.id = `slot-${slot.slot_id}`;
        if (!slot.available) li.classList.add("unavailable");
        ul.appendChild(li);

        // Click listener for toggling availability
        li.addEventListener("click", () => {
          const status = li.classList.contains("unavailable")
            ? "True"
            : "False";
          fetch("/data/time-slot", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: li.id, status }),
          });
          li.classList.toggle("unavailable");
        });
      } else {
        // Update availability if it changed
        if (slot.available && li.classList.contains("unavailable"))
          li.classList.remove("unavailable");
        else if (!slot.available && !li.classList.contains("unavailable"))
          li.classList.add("unavailable");
      }
    });
  }

  // Show/hide navigation
  nextButton.classList.toggle("show", currentWeek < 3);
  prevButton.classList.toggle("show", currentWeek > 0);
}

// Initial render
getWeek(currentWeek);

// Poll current week every 5 seconds
setInterval(() => getWeek(currentWeek), 5000);

// Navigation buttons
prevButton.addEventListener("click", () => {
  currentWeek--;
  getWeek(currentWeek);
});
nextButton.addEventListener("click", () => {
  currentWeek++;
  getWeek(currentWeek);
});

// Theme toggle
themeToggle.addEventListener("click", () => {
  body.setAttribute(
    "data-theme",
    body.getAttribute("data-theme") === "dark" ? "" : "dark"
  );
});
