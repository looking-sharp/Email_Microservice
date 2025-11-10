'use strict';

const form = document.getElementById("emailForm");
const isTimedCheckbox = document.getElementById("is_timed");
const timedSection = document.querySelector(".timed_section");
const dateInput = document.getElementById("schedule_for_date");
const timeInput = document.getElementById("schedule_for_time");
const bodyInput = document.getElementById("emailBody");
const tzSelect = document.getElementById("timezone");
const response = document.getElementById("Response");

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
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    bodyInput.value = quill.root.innerHTML;

    const isEmpty = quill.getText().trim().length === 0;
    if(isEmpty) {
        alert("Email body cannot be empty.");
        return false;
    }

    let payload = {
        recipient: form.recipiant.value,
        subject: form.subject.value,
        body: bodyInput.value,
        is_timed: isTimedCheckbox.checked
    };
    console.log(payload);

    if (isTimedCheckbox.checked) {
        const date = dateInput.value;
        const time = timeInput.value;
        const tz = tzSelect.value;

        if (!date || !time) {
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
        const timeValue = `${String(hh).padStart(2,"0")}:${String(mm).padStart(2,"0")}`;
        payload.date_to_send = date;
        payload.time_to_send = timeValue;
    }

    try {
        const res = await fetch("/send-test-email", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        response.textContent = JSON.stringify(data, null, 2); // display response in your <pre>
    } catch (err) {
        console.error("Error sending email:", err);
        response.textContent = "Error: " + err;
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