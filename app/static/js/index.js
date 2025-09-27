// Connect to the WebSocket server
var socketProtocol = location.protocol === 'https:' ? 'wss://' : 'ws://';
var socket = io.connect(socketProtocol + document.domain + ':' + location.port);


function updateSabah() {
    var sabahText = document.getElementById("sabah-input").value;
    // Emit the 'update_sabah' event to the server with the new sabah text
    socket.emit('update_sabah', { sabah: sabahText });
}
// Event listener
socket.on('sabah_updated', data => {
    console.log(data.message);
});


// initial emit for newsflash
socket.emit('get_newsflash');
// Event listener to handle incoming newsflash data from the server
socket.on('newsflash_data', data => {
    // Extract the newsflash entries from the received data
    const entries = data.entries;
    console.log(entries);

    // Update the newsflash list with the received entries
    updateNewsflashList(entries);
});

// Function to update the newsflash list with the given entries
function updateNewsflashList(entries) {
    var ul = document.getElementById('newsflash-ul');
    ul.innerHTML = ''; // Clear existing entries

    // Populate the list with the newsflash entries
        entries.forEach(entry => {
            addNewsflashEntry(entry);
        });
}

// Function to add a new newsflash entry to the database
function addNewsflashEntryToDB(newEntry) {
    socket.emit('add_newsflash', { newsflashText: newEntry });
}


// Function to add a new newsflash entry to the list
function addNewsflashEntry(entry) {
    var ul = document.getElementById('newsflash-ul');
    var li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';

    // Create a text node for the entry and append it to the li element
    var entryTextNode = document.createTextNode(entry);
    li.appendChild(entryTextNode);

    // Add a button to remove the entry
    var button = document.createElement('button');
    button.className = 'btn btn-danger btn-sm';
    button.textContent = 'Sil';
    button.addEventListener('click', function () {
        // Handle removal when the button is clicked
        removeNewsflashEntry(entry);
    });

    li.appendChild(button);
    ul.appendChild(li);
}


// Function to remove a newsflash entry from the database
function removeNewsflashEntryFromDB(entry) {
    socket.emit('remove_newsflash', { newsflashText: entry });
}

// Function to remove a newsflash entry
function removeNewsflashEntry(entry) {
    removeNewsflashEntryFromDB(entry); // Remove the entry from the database
    //reloadPage();
}

// Function to reload the page after a delay (in milliseconds)
function reloadPage() {
    setTimeout(function () {
        location.reload();
    }, 1000); // Adjust the delay as needed
}