window.onload = init;

function init() {

    console.log("init")
    // Get the movie ID from a data attribute or any other method you prefer
    const movie_id = document.body.getAttribute('data-movie-id');

// Fetch movie details from the server
fetch(`/movie_details/${movie_id}`)
    .then(response => response.json())
    .then(data => {
        console.log({data})
        // add board count
        let boredCount = data.emotion_chart.boredCount?.toFixed(1);
        let boardCountDiv = document.getElementById("boardCount");
        if (boardCountDiv) {
            boardCountDiv.innerHTML = `Average tiredness/boredom count: #${boredCount}`
        }

        // Populate movie details top-title
        document.getElementById('clipTitle').innerText = data.title;
        document.getElementById('top-title').innerText = data.title;
        document.getElementById('videoClip').src = `../static/film/${data.FilmFile}`;
        console.log(`../static/film/${data.FilmFile}`)
        document.getElementById('clipDescription').innerText = `Genre: ${data.genre} \n Release date: ${data.release_date} \n ${data.description}`;

        // Populate emotion rates
        const emotionLabels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise'];
        let emotions = {}
        let totalEmotionValue = 0;
        emotionLabels.forEach((emotion) => {
            emotions[emotion] = data.emotion_chart[emotion];
            totalEmotionValue += data.emotion_chart[emotion];
        });

        // Calculate scaling factor
        const scalingFactor = totalEmotionValue > 0 ? 1 / totalEmotionValue : 0;

        const progressBars = document.querySelectorAll('.progress-bar');
        const emotionColors = ['bg-danger', 'bg-success', 'bg-info', 'bg-warning', 'bg-primary', 'bg-secondary'];
        progressBars.forEach((bar, index) => {
            const emotion = emotionLabels[index];
            const value = emotions[emotion] * scalingFactor * 100; // Adjusted percentage
            bar.style.width = `${value}%`;
            bar.setAttribute('aria-valuenow', value.toFixed(1));
            bar.className = `progress-bar ${emotionColors[index]}`; // Update the class for the color
        });

        const emotion_text = document.querySelectorAll('.emotion-text');
        emotion_text.forEach((text, index) => {
            const emotion = emotionLabels[index];
            const value = emotions[emotion] * scalingFactor * 100; // Adjusted percentage
            text.innerText = `${formatNumber(value)}% - ${emotion.charAt(0).toUpperCase() + emotion.slice(1)}`;
        });

        function formatNumber(num) {
            let [integer, decimal] = num.toFixed(1).split('.');
            integer = integer.padStart(2, '0');
            return `${integer}.${decimal}`;
        }

    })
    .catch(error => console.error('Error fetching movie details:', error));

    // Add event listener to redirect button
    const redirectButton = document.getElementById("redirectToFormBtn");
    if (redirectButton) {
        redirectButton.addEventListener("click", function () {
            window.location.href = "/feedbackForm";
        });
    }

}
