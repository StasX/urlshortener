// Check if url valid
const isUrl = (url) => /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/.test(url);

// Keep success results and errors visually distinct.
function showResult(selector, text, isError = false) {
    $(selector).val(text).text(text)
        .toggleClass("error-message", isError)
        .attr("role", isError ? "alert" : "status")
        .css({ display: "block" });
}
function showFullUrl(text, isError = false) {
    showResult("#result", text, isError);
}
function showShortedUrl(text, isError = false) {
    showResult("#shortedUrl", text, isError);
}

// Get Full Url
function getFullUrl(url) {
    $.post("/geturl", { "url": url })
        .done((data) => showFullUrl(data.url))
        .fail((err) => showFullUrl(err.responseJSON?.error || "Could not reveal this link. Please try again.", true));
}

function reverse() {
    const url = $("#url").val();
    isUrl(url) ? getFullUrl(url) : showFullUrl("Enter a valid HTTP or HTTPS URL.", true);
}

// Generate Short Url
function getShortUrl(url) {

    $.post("/short", { "url": url })
        .done((data) => showShortedUrl(data.url))
        .fail((err) => showShortedUrl(err.responseJSON?.error || "Could not shorten this link. Please try again.", true));
}

function shortIt() {
    const url = $("#fullUrl").val();
    isUrl(url) ? getShortUrl(url) : showShortedUrl("Enter a valid HTTP or HTTPS URL.", true);
}

// Add handler for logout
function logout() {
    const url = `${location.origin}/logout`;
    $("#globalError").prop("hidden", true);
    $.ajax({ url: url, method: "DELETE" })
        .done(() => {
            $("#dashboardLink").remove();
            if (location.href != `${location.origin}/home`) location.href = `${location.origin}/home`;
            $("#helloUser").text("Hello Guest");
            $("#auth").html(`<a href="${location.origin}/login">Sign in</a>`)
        })
        .fail((response) => {
            $("#globalError").text(response.responseJSON?.error || "Could not sign out. Please try again.").prop("hidden", false);
        });
}


function removeUrl(id, button, error) {
    button.prop("disabled", true);
    error.text("");
    $.ajax({ url: `/urls/${encodeURIComponent(id)}`, method: "DELETE" })
        .done(() => location.reload())
        .fail((response) => {
            error.text(response.responseJSON?.error || "Could not remove the link. Please try again.");
            button.prop("disabled", false);
        });
}

//Generate url card
function generateCard(data) {
    const card = $("<div>").addClass("card");
    const body = $("<div>").addClass("card-body").appendTo(card);
    for (const [label, value, classes] of [
        ["Short link:", data.shortUrl, "mt-2"],
        ["Destination:", data.fullUrl, "mt-2"],
        ["Visits:", data.visits, "mt-2 mb-4"],
    ]) {
        const row = $("<div>").addClass(classes).appendTo(body);
        $("<b>").text(label).appendTo(row);
        row.append(document.createTextNode(` ${value}`));
    }
    const actions = $("<div>").appendTo(body);
    const error = $("<div>").addClass("error-message").attr("role", "alert").appendTo(actions);
    const button = $("<button>").addClass("btn btn-md btn-danger")
        .attr("type", "button").text("Remove link ")
        .on("click", () => removeUrl(data.id, button, error)).appendTo(actions);
    $("<i>").addClass("fa-solid fa-xmark").appendTo(button);
    return card;
}


// Load document
$(document).ready(() => {
    // Add handlers to buttons and inputs
    $("#reverse").click(reverse);
    $("#url").on('keypress', function (e) {
        if (e.which == 13) reverse();
    });
    $("#shortIt").click(shortIt);
    $("#fullUrl").on('keypress', function (e) {
        if (e.which == 13) shortIt();
    });
    // Display statistics.
    const pie = $("#urlsPie");
    const urlsContainer = $("#urlsContainer");
    if (pie.length) {
        $.get("/urls-stat").done(data => {
            $("#linksStatus").text(data.length ? "" : "No links yet. Create your first short link to get started.");
            if (data.length) $("#linksStatus").remove();
            data.forEach(item => urlsContainer.append(generateCard(item)));
            if (!data.some(item => item.visits > 0)) {
                pie.hide();
                $("#chartStatus").text("Your chart will appear when your links receive their first visit.");
                return;
            }
            const palette = ["#9ac9a5", "#538365", "#c1d8ae", "#6eaaa0", "#85975e", "#385e48"];
            new Chart(pie[0].getContext("2d"), {
                type: "doughnut",
                data: {
                    labels: data.map(item => item.shortUrl),
                    datasets: [{
                        data: data.map(item => item.visits),
                        backgroundColor: data.map((_, index) => palette[index % palette.length]),
                        borderColor: "#13251b",
                        borderWidth: 4,
                    }],
                },
                options: {
                    responsive: true,
                    cutoutPercentage: 70,
                    legend: { position: "bottom", labels: { boxWidth: 10, padding: 18, fontColor: "#a6bbae" } },
                },
            });
        }).fail(() => {
            $("#linksStatus").removeClass("empty-state").addClass("error-message").attr("role", "alert").text("Could not load your links. Please refresh to try again.");
            pie.hide();
            $("#chartStatus").addClass("error-message").attr("role", "alert").text("Statistics are temporarily unavailable.");
        });
    }
});
