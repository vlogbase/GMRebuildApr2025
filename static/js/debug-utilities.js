/**
 * Debug Utilities Module
 * Handles debugging functionality for development
 */

document.addEventListener("DOMContentLoaded", function () {
    console.log('🔍 Searching DOM for "Almost Ready" message...');

    // Search all text nodes in the document for "Almost Ready" text
    let found = false;
    const searchText = function (element) {
        if (element.nodeType === Node.TEXT_NODE) {
            if (element.textContent.includes("Almost Ready")) {
                console.log('🎯 Found "Almost Ready" text in:', element);
                console.log("📌 Parent element:", element.parentNode);
                found = true;
            }
        } else {
            for (let i = 0; i < element.childNodes.length; i++) {
                searchText(element.childNodes[i]);
            }
        }
    };

    // Give a slight delay for all content to load, including any dynamically added content
    setTimeout(function () {
        searchText(document.body);
        if (!found) {
            console.log('❌ No "Almost Ready" text found in the DOM.');
        }
    }, 1000);
});