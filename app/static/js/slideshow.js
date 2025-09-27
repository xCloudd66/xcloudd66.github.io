// Connect to the WebSocket server
var socketProtocol = location.protocol === 'https:' ? 'wss://' : 'ws://';
var socket = io.connect(socketProtocol + document.domain + ':' + location.port);

// ****** AUTOMATIC DAILY RELOAD
// Function to reload the page after a specified time interval
function reloadAtNextDay() {
    const now = new Date();
    const millisecondsUntilNextDay = 24 * 60 * 60 * 1000 - (now % (24 * 60 * 60 * 1000));
    setTimeout(reloadPage, millisecondsUntilNextDay);
    console.log('Now is ' + now + ' and reloading page in ' + Math.round((millisecondsUntilNextDay/1000/60/60) * 100) / 100 + ' hours.');
}

function reloadPage() {
    location.reload();
}

// Call reloadAtNextDay to schedule the page reload at the next day
reloadAtNextDay();


//+++++++++++ SLIDESHOW FUNCTIONS +++++++++++++++
// Event listener
socket.on('file_changed', data => {
    location.reload();
    console.log(data.message);
});

// Global variable to track if a video is currently playing
var isVideoPlaying = false;

// Listen for the carousel slide event
$('#slideshow-container').on('slide.bs.carousel', function (event) {
    var $slide = $(event.relatedTarget); // Get the current slide element
    var $video = $slide.find('video'); // Get the video element within the current slide

    // If the current slide contains a video
    if ($video.length) {
        // Pause all videos before moving to the next slide
        $('video').each(function() {
            this.pause();
        });

        // Pause the carousel
        $('#slideshow-container').carousel('pause');

        // Play the video
        $video.get(0).play();
        isVideoPlaying = true;

        // Listen for the video ended event
        $video.on('ended', function () {
            // Resume carousel sliding after the video ends
            $('#slideshow-container').carousel('cycle');
            isVideoPlaying = false;
        });
    } else {
        // If no video is present, resume carousel sliding
        if (!isVideoPlaying) {
            $('#slideshow-container').carousel('cycle');
        }
    }
});

// Listen for the carousel sliding event
$('#slideshow-container').on('slid.bs.carousel', function () {
    // If a video is currently playing, prevent the carousel from sliding
    if (isVideoPlaying) {
        $('#slideshow-container').carousel('pause');
    }
});


//+++++++++++ CLOCK FUNCTIONS +++++++++++++++
function updateDigitalClock() {
    var clockElement = document.getElementById('digital-clock');
    var currentTime = new Date();
    var hours = currentTime.getHours();
    var minutes = currentTime.getMinutes();
    var seconds = currentTime.getSeconds();

    // Format the time with leading zeros
    var formattedTime = formatTime(hours) + ':' + formatTime(minutes) + ':' + formatTime(seconds);

    // Update the clock element
    clockElement.textContent = formattedTime;

}

function formatTime(time) {
    return (time < 10 ? '0' : '') + time;
}

setInterval(updateDigitalClock, 1000);
updateDigitalClock();


//+++++++++++ EVENTS FUNCTIONS +++++++++++++++

//+++++++++++ SABAH +++++++++++++
// Event listener
socket.on('sabah_updated', data => {
    console.log(data.message);
    location.reload();
});


//+++++++++++ NEWSFLASH +++++++++++++++
socket.emit('get_newsflash');

// Event listener to handle incoming newsflash data from the server
socket.on('newsflash_data', data => {
    // Extract the newsflash entries from the received data
    const entries = data.entries;
    console.log(entries);

    // Update the newsflash marquee
    displayNewsflashInMarquee(data.entries);
});


// Function to display newsflash entries in the marquee
function displayNewsflashInMarquee(entries) {
    const marquee = document.getElementById('newsflash-marquee');
    marquee.innerHTML = ''; // Clear existing entries

    entries.forEach(entry => {
        const span = document.createElement('span');
        span.textContent = entry + ' +++ ';
        marquee.appendChild(span);
    });
}



// Fetch the event times only once
fetch('/get_event_times')
    .then(response => response.json())
    .then(data => {
        const eventTimesData = data.event_times_values;
        const eventTimesForToday = eventTimesData[0];
        const eventTimesForTomorrow = eventTimesData[1];

        // Update the remaining time initially and every second
        updateRemainingTime(eventTimesForToday, eventTimesForTomorrow);
        setInterval(() => updateRemainingTime(eventTimesForToday, eventTimesForTomorrow), 1000); // Update every second
    });



function updateRemainingTime(eventTimesForToday, eventTimesForTomorrow) {
    const now = new Date();
    const currentTime = now.getHours() * 60 * 60 + now.getMinutes() * 60 + now.getSeconds();

    // Find the next event time for today
    let nextEventTimeForToday = null;
    for (const eventTime of eventTimesForToday) {
        const [hours, minutes] = eventTime.split(':');
        const eventSeconds = parseInt(hours) * 60 * 60 + parseInt(minutes) * 60;
        if (eventSeconds > currentTime) {
            nextEventTimeForToday = eventSeconds;
            break;
        }
    }

    // Find the first event time for tomorrow
    const firstEventTimeForTomorrow = eventTimesForTomorrow[0];
    const [hours, minutes] = firstEventTimeForTomorrow.split(':');
    const nextEventTimeForTomorrow = parseInt(hours) * 60 * 60 + parseInt(minutes) * 60 + 24 * 60 * 60; // Add 24 hours for tomorrow

    // Choose the next event time based on whether there are events left for today
    const nextEventTime = nextEventTimeForToday !== null ? nextEventTimeForToday : nextEventTimeForTomorrow;

    const remainingSeconds = nextEventTime - currentTime;
    const remainingHours = Math.floor(remainingSeconds / 3600);
    const remainingMinutes = Math.floor((remainingSeconds % 3600) / 60);
    const remainingSecondsInMinute = remainingSeconds % 60;

    // Update the displayed remaining time
    const remainingTimeElement = document.getElementById('remaining-time');
    remainingTimeElement.textContent = `${remainingHours} saat ${remainingMinutes} dak. ${remainingSecondsInMinute} san.`;




}