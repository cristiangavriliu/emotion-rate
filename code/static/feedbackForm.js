window.onload = init;

function init() {
    console.log("init")
           const formId = localStorage.getItem('emotionRecordingId');
        if (formId) {
            document.getElementById('formId').value = formId;
        }

    const webUserQuestions = [
        "The website has a user friendly interface.",
        "The website is easy to navigate.",
        "The content on the website is informative.",
        "The website has a pleasing color scheme.",
        "I would recommend this website to others."
    ];

    const SUSQuestions = [
        "I think I would like to use the app frequently.",
        "I found the app unnecessarily complex.",
        "I found the app easy to use.",
        "I think I would need the help of a technically competent person to be able to use the app.",
        "I think the various functions in the app were well integrated.",
        "I think the app contained too many inconsistencies.",
        "I can imagine that most people learn how to use the app very quickly.",
        "I found the app very cumbersome to use.",
        "I felt safe using the app.",
        "I think I would have to learn a lot before I could start using the app.",
        "Overall, I would rate the usability of the application as ..."
    ]; 
    const emotionQuestions = [
        "Angry",
        "Disgust",
        "Fear",
        "Happy",
        "Sad",
        "Surprise",
        "Tired/Bored"
    ];

    const webUserContainer = document.getElementById('web-user-questions');
    const SUSContainer = document.getElementById('sus-questions');
    const emotionContainer = document.getElementById('emotion-questions');

    webUserQuestions.forEach((question, index) => {
        const questionNumber = index + 1;
        const questionId = `q${questionNumber}`;

        const questionDiv = document.createElement('div');
        questionDiv.className = 'question';

        const label = document.createElement('label');
        label.setAttribute('for', questionId);
        label.textContent = `${questionNumber}. ${question}`;

        const likertDiv = document.createElement('div');
        likertDiv.className = 'likert';

        for (let i = 1; i <= 5; i++) {
            const radioLabel = document.createElement('label');
            const radioInput = document.createElement('input');
            radioInput.type = 'radio';
            radioInput.name = questionId;
            radioInput.value = i;

            radioLabel.appendChild(radioInput);
            radioLabel.appendChild(document.createTextNode(getWebUserLikertLabel(i)));
            likertDiv.appendChild(radioLabel);
        }

        questionDiv.appendChild(label);
        questionDiv.appendChild(likertDiv);
        webUserContainer.appendChild(questionDiv);
    });

    SUSQuestions.forEach((question, index) => {
        const questionNumber = index + 1;
        const questionId = `sus${questionNumber}`;

        const questionDiv = document.createElement('div');
        questionDiv.className = 'question';

        const label = document.createElement('label');
        label.setAttribute('for', questionId);
        label.textContent = `${questionNumber}. ${question}`;

        const likertDiv = document.createElement('div');
        likertDiv.className = 'likert';

        if (question === "Overall, I would rate the usability of the application as ...") {
            const options = ["Awful", "Bad", "Ok", "Good", "Excellent"];
            options.forEach((option, i) => {
                const radioLabel = document.createElement('label');
                const radioInput = document.createElement('input');
                radioInput.type = 'radio';
                radioInput.name = questionId;
                radioInput.value = option;

                radioLabel.appendChild(radioInput);
                radioLabel.appendChild(document.createTextNode(option));
                likertDiv.appendChild(radioLabel);
            });
        } else {
            for (let i = 1; i <= 5; i++) {
                const radioLabel = document.createElement('label');
                const radioInput = document.createElement('input');
                radioInput.type = 'radio';
                radioInput.name = questionId;
                radioInput.value = i;

                radioLabel.appendChild(radioInput);
                radioLabel.appendChild(document.createTextNode(getWebUserLikertLabel(i)));
                likertDiv.appendChild(radioLabel);
            }
        }
        questionDiv.appendChild(label);
        questionDiv.appendChild(likertDiv);
        SUSContainer.appendChild(questionDiv);
    }); 


    emotionQuestions.forEach((question, index) => {
        const questionNumber = index + 1;
        const questionId = `emotion${questionNumber}`;

        const questionDiv = document.createElement('div');
        questionDiv.className = 'question';

        const label = document.createElement('label');
        label.setAttribute('for', questionId);
        label.textContent = `${questionNumber}. ${question}`;
        label.style.paddingRight = "10px"
 
        const sliderContainer = document.createElement('div');
        sliderContainer.className = 'slider-container';

        const sliderInput = document.createElement('input');
        sliderInput.type = 'range';
        sliderInput.name = questionId;
        sliderInput.id = questionId;
        sliderInput.min = '0';
        sliderInput.max = '1';
        sliderInput.step = '0.01';
        sliderInput.className = 'slider';
        sliderInput.value = '0';

        const valueLabel = document.createElement('span');
        valueLabel.id = `${questionId}-value`;
        valueLabel.textContent = '0%'; // Initial value as 0%

        sliderInput.addEventListener('input', () => {
            const percentageValue = Math.round(sliderInput.value * 100); // Convert to percentage
            valueLabel.textContent = `${percentageValue}%`;
        });

        sliderContainer.appendChild(sliderInput);


        questionDiv.appendChild(label);
        questionDiv.appendChild(valueLabel);
        questionDiv.appendChild(sliderContainer);
        emotionContainer.appendChild(questionDiv); 

       /* const likertDiv = document.createElement('div');
        likertDiv.className = 'likert';

        for (let i = 1; i <= 5; i++) {
            const radioLabel = document.createElement('label');
            const radioInput = document.createElement('input');
            radioInput.type = 'radio';
            radioInput.name = questionId;
            radioInput.value = i;

            radioLabel.appendChild(radioInput);
            radioLabel.appendChild(document.createTextNode(getWebUserLikertLabel(i)));
            likertDiv.appendChild(radioLabel);
        }

        questionDiv.appendChild(label);
        questionDiv.appendChild(likertDiv);
        emotionContainer.appendChild(questionDiv); */
    });

    function getWebUserLikertLabel(value) {
        switch (value) {
            case 1:
                return 'Strongly Disagree';
            case 2:
                return 'Disagree';
            case 3:
                return 'Neutral';
            case 4:
                return 'Agree';
            case 5:
                return 'Strongly Agree';
        }
    }
}
