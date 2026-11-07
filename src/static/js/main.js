// Check if url valid
const isUrl = (url) => /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/.test(url);

// Display full Url
function showFullUrl(txt) {
    const result = $("#result");
    result.val(txt);
    result.css({ "display": "block" });
}
// Display short Url
function showShortedUrl(txt) {
    const shortUrl = $("#shortedUrl");
    shortUrl.val(txt);
    shortUrl.css({ "display": "block" });
}

// Get Full Url
function getFullUrl(url) {
    $.post("/geturl", { "url": url })
        .done((data) => showFullUrl(data.url))
        .fail((err) => showFullUrl("Something went wrong."));
}

function reverse() {
    const url = $("#url").val();
    isUrl(url) ? getFullUrl(url) : showFullUrl("Invalid url.");
}

// Generate Short Url
function getShortUrl(url) {

    $.post("/short", { "url": url })
        .done((data) => showShortedUrl(data.url))
        .fail((err) => showShortedUrl("Something went wrong."));
}

function shortIt() {
    const url = $("#fullUrl").val();
    isUrl(url) ? getShortUrl(url) : showShortedUrl("Invalid url.");
}

// Add handler for logout
function logout() {
    const url = `${location.origin}/logout`;
    $.ajax({ url: url, method: "DELETE" })
        .done(() => {
            $("#dashboardLink").remove();
            if (location.href != `${location.origin}/home`) location.href = `${location.origin}/home`;
            $("#helloUser").text("Hello Guest");
            $("#auth").html(`<a href="${location.origin}/login">Sign in</a>`)
        });
}


//Generate url card
function generateCard(data) {
    const card = $("<div>").addClass("card col-md-8 offset-md-2");
    const body = $("<div>").addClass("card-body").appendTo(card);
    for (const [label, value, classes] of [
        ["Shorted url:", data.shortUrl, "mt-2"],
        ["Full url:", data.fullUrl, "mt-2"],
        ["Visits:", data.visits, "mt-2 mb-4"],
    ]) {
        const row = $("<div>").addClass(classes).appendTo(body);
        $("<b>").text(label).appendTo(row);
        row.append(document.createTextNode(` ${value}`));
    }
    const actions = $("<div>").appendTo(body);
    const button = $("<button>").addClass("btn btn-md btn-danger")
        .text("Remove link ").on("click", () => removeUrl(data.id)).appendTo(actions);
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
    // Display statistics
    const pie = $("#urlsPie");
    const urlsContainer = $("#urlsContainer");
    if (Array.from(pie).length) {
        const ctx = pie[0].getContext('2d');
        $.get(`${location.origin}/urls-stat`).done(data => {
            const labels = [];
            const visits = [];
            $.each(data, function (index, item) {
                urlsContainer.append(generateCard(item));
                labels.push(item.shortUrl)
                visits.push(item.visits)
            });
            new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: visits,
                        backgroundColor: [
                            "rgba(255, 99, 71, 0.2)",
                            "rgba(135, 206, 235, 0.2)",
                            "rgba(75, 0, 130, 0.2)",
                            "rgba(255, 215, 0, 0.2)",
                            "rgba(34, 139, 34, 0.2)",
                            "rgba(255, 105, 180, 0.2)",
                            "rgba(240, 230, 140, 0.2)",
                            "rgba(70, 130, 180, 0.2)",
                            "rgba(210, 105, 30, 0.2)",
                            "rgba(128, 0, 128, 0.2)",
                            "rgba(255, 182, 193, 0.2)",
                            "rgba(30, 144, 255, 0.2)",
                            "rgba(144, 238, 144, 0.2)",
                            "rgba(255, 160, 122, 0.2)",
                            "rgba(186, 85, 211, 0.2)",
                            "rgba(72, 61, 139, 0.2)",
                            "rgba(255, 69, 0, 0.2)",
                            "rgba(173, 216, 230, 0.2)",
                            "rgba(123, 104, 238, 0.2)",
                            "rgba(0, 255, 127, 0.2)",
                            'rgba(255, 255, 0, 0.2)',
                            'rgba(0, 255, 255, 0.2)',
                            'rgba(255, 20, 147, 0.2)',
                            'rgba(0, 100, 0, 0.2)',
                            'rgba(255, 99, 132, 0.2)',
                            'rgba(255, 69, 0, 0.2)',
                            'rgba(199, 21, 133, 0.2)',
                            'rgba(255, 140, 0, 0.2)',
                            'rgba(0, 191, 255, 0.2)',
                            'rgba(147, 112, 219, 0.2)',
                        ],
                        borderColor: [
                            "rgb(255, 99, 71)",
                            "rgb(135, 206, 23)",
                            "rgb(75, 0, 130)",
                            "rgb(255, 215, 0)",
                            "rgb(34, 139, 34)",
                            "rgb(255, 105, 180)",
                            "rgb(240, 230, 140)",
                            "rgb(70, 130, 180)",
                            "rgb(210, 105, 30)",
                            "rgb(128, 0, 128)",
                            "rgb(255, 182, 193)",
                            "rgb(30, 144, 255)",
                            "rgb(144, 238, 144)",
                            "rgb(255, 160, 122)",
                            "rgb(186, 85, 211)",
                            "rgb(72, 61, 139)",
                            "rgb(255, 69, 0)",
                            "rgb(173, 216, 230)",
                            "rgb(123, 104, 238)",
                            "rgb(0, 255, 127)",
                            'rgb(255, 255, 0)',
                            'rgb(0, 255, 255)',
                            'rgb(255, 20, 147)',
                            'rgb(0, 100, 0)',
                            'rgb(255, 99, 132)',
                            'rgb(255, 69, 0)',
                            'rgb(199, 21, 133)',
                            'rgb(255, 140, 0)',
                            'rgb(0, 191, 255)',
                            'rgb(147, 112, 219)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    }
                }
            });
        }).fail(err => {

        });
    }
});
