const sortOptionsDiv = document.getElementById("sort-list");
const sortButton = document.getElementById("sortByBtn");
var sortOptions = ["Oldest", "Newest", "Email Status"];
var divShowing = false;

function sortEmailsBy(sortingMethod) {
    const emailEntries = Array.from(document.querySelectorAll('.email-entry'));
    if (emailEntries.length === 0) return;
    let sorted = [];
    switch (sortingMethod) {
        case "Newest":
            sorted = emailEntries.sort((a, b) => {
                const dateA = new Date(a.querySelector('.date_sent').textContent.replaceAll('"', '') + ' ' + a.querySelector('.time_sent').textContent.replaceAll('"', ''));
                const dateB = new Date(b.querySelector('.date_sent').textContent.replaceAll('"', '') + ' ' + b.querySelector('.time_sent').textContent.replaceAll('"', ''));
                return dateB - dateA; // newest first
            });
            break;

        case "Oldest":
            sorted = emailEntries.sort((a, b) => {
                const dateA = new Date(a.querySelector('.date_sent').textContent.replaceAll('"', '') + ' ' + a.querySelector('.time_sent').textContent.replaceAll('"', ''));
                const dateB = new Date(b.querySelector('.date_sent').textContent.replaceAll('"', '') + ' ' + b.querySelector('.time_sent').textContent.replaceAll('"', ''));
                return dateA - dateB; // oldest first
            });
            break;

        case "Email Status":
            sorted = emailEntries.sort((a, b) => {
                const statusA = parseInt(a.querySelector('.status_code').textContent);
                const statusB = parseInt(b.querySelector('.status_code').textContent);
                return statusA - statusB;
            });
            break;

        default:
            console.warn("Unknown sorting method:", sortingMethod);
            return;
    }
    const parent = emailEntries[0].parentElement;
    sorted.forEach(el => parent.appendChild(el));

    toggleDivDisplay();
}


document.addEventListener('DOMContentLoaded', () => {
    sortOptions.forEach(element => {
        const div = document.createElement('div');
        div.textContent = element;

        div.addEventListener('click', () => {
            sortEmailsBy(`${element}`);
        });

        sortOptionsDiv.appendChild(div);
    });
});

function toggleDivDisplay() {
    divShowing = !divShowing;
    sortOptionsDiv.style.display = divShowing? "block" : "none";
    const sortArrow = document.getElementById("sortArrow");
    sortArrow.classList.toggle("open");
}

sortButton.addEventListener('click', () => {
    toggleDivDisplay();
})

