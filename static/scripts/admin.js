const emailEntries = document.querySelectorAll(".email-entry");

function toggleDetails(id) {
    const details = document.getElementById(`details-${id}`);
    const arrow = document.getElementById(`arrow-${id}`);
    if (details.style.display === "block") {
        details.style.display = "none";
        arrow.classList.remove("open");
    } else {
        details.style.display = "block";
        arrow.classList.add("open");
    }
}

const colapseButton = document.getElementById("colapseBtn");
const expandButton = document.getElementById("expandBtn");

colapseButton.addEventListener('click', () => {
    emailEntries.forEach(entry => {
        const details = entry.querySelector(".details");
        if(details.style.display === "block") {
            toggleDetails(details.id.replace("details-", ""))
        }
    });
});

expandButton.addEventListener('click', () => {
    emailEntries.forEach(entry => {
        const details = entry.querySelector(".details");
        if(details.style.display === "none") {
            toggleDetails(details.id.replace("details-", ""))
        }
    });
});

const searchButton = document.getElementById("searchBtn");
const filterText = document.getElementById("filter-text");

function filter() {
    const query = filterText.value.trim();
    if (!query) {
        emailEntries.forEach(e => e.style.display = "block");
        return;
    }

    // Split by ":" and remove quotes / "INCLUDES"
    const queryFormatted = query.split(":").map(substr => substr.replace(/"/g, "").replace("INCLUDES", "").trim());
    const key = queryFormatted[0];
    const value = queryFormatted[1] ? queryFormatted[1].toLowerCase() : "";
    const partial = query.toUpperCase().includes("INCLUDES");
    console.log(`Looking for ${partial ? "partial" : "exact"} match for ${key} with value ${value}`)

    emailEntries.forEach(entry => {
        const element = entry.querySelector(`.${key}`);
        let text = element ? element.textContent.replace(/"/g, "").trim() : "";
        console.log(text);

        // Handle null values
        if (text.toLowerCase() === "null") text = "";

        if (partial) {
            // Partial, case-insensitive match
            if (text.toLowerCase().includes(value)) {
                entry.style.display = "block";
            } else {
                entry.style.display = "none";
            }
        } else {
            // Exact match, case-insensitive
            if (text.toLowerCase() === value) {
                entry.style.display = "block";
            } else {
                entry.style.display = "none";
            }
        }
    });
}


filterText.addEventListener('keydown', function(event) {
    if(event.key === "Enter") {
        filter();
    }
});

searchButton.addEventListener('click', () => {
    filter();
})