'use strict';

const form = document.getElementById("emailForm");

form.addEventListener("submit", (e) => {
    document.getElementById("emailBody").value = quill.root.innerHTML;

    const isEmpty = quill.getText().trim().length === 0;
    if(isEmpty) {
        e.preventDefault();
        alert("Email body cannot be empty.");
        return false;
    }
});