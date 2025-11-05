'use strict';

const form = document.getElementById("emailForm");
const isTimedCheckbox = document.getElementById("is_timed");
const timedSection = document.querySelector(".timed_section");
const dateInput = document.getElementById("schedule_for_date");
const timeInput = document.getElementById("schedule_for_time");
const bodyInput = document.getElementById("emailBody");
const tzSelect = document.getElementById("timezone");

const tzOffsets = {
  "UTC": 0,
  "America/Los_Angeles": -8,
  "America/New_York": -5,
  "Europe/London": 0,
  "Asia/Tokyo": 9
};

/** This function controls the data formatting from the HTML form
 *  so that it is understandable by the flask route.
 */
form.addEventListener("submit", (e) => {
    bodyInput.value = quill.root.innerHTML;

    const isEmpty = quill.getText().trim().length === 0;
    if(isEmpty) {
        e.preventDefault();
        alert("Email body cannot be empty.");
        return false;
    }

    if (isTimedCheckbox.checked) {
        const date = dateInput.value;
        const time = timeInput.value;
        const tz = tzSelect.value;

        if (!date || !time) {
            e.preventDefault();
            alert("Please select both a date and time for the timed email.");
            return;
        }

        const [hours, minutes] = time.split(":").map(Number);

        const offset = tzOffsets[tz];
        if (offset === undefined) {
            e.preventDefault();
            alert("Unsupported timezone selected.");
            return;
        }

        const hh = (hours - offset + 24) % 24;
        const mm = minutes;

        //console.log(`${String(hh).padStart(2,"0")}:${String(mm).padStart(2,"0")}`);
        timeInput.value = `${String(hh).padStart(2,"0")}:${String(mm).padStart(2,"0")}`;
    }
});

/* Hide the timed section by default*/
timedSection.style.display = "none";

/* Toggle visibility when "Timed Email" checkbox changes */
isTimedCheckbox.addEventListener("change", function () {
  timedSection.style.display = this.checked ? "flex" : "none";
  timedSection.style.gap = "8px";
  timedSection.style.alignItems = "center";
});