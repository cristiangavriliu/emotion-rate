from flask import Flask, render_template, Response, jsonify, request,  url_for,redirect
from camera import VideoCamera

# ---------------------------- DB
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

# Configuration for MongoDB with TLS enabled.
# TODO Replace the connection string with your own.
client = MongoClient("Insert your MongoDB connection string here")
db = client.myDatabase
emotion_records_collection = db.emotionRecords
# test the db connection
try:
    # Ping the database to ensure the connection is established
    client.admin.command('ping')
    print("MongoDB connection established successfully.")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
# ----------------------------

from button_toggle import ButtonToggle

app = Flask(__name__)
button_toggle = ButtonToggle()
camera2 = VideoCamera()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/clip/<movie>')
def view_clip(movie):
    # You can now use the 'name' variable in your function
    return render_template('view_clip.html', movie=movie)

@app.route('/new_recording/<movie>')
def new_recording(movie):
    # You can now use the 'name' variable in your function
    return render_template('new_recording.html', movie=movie)

@app.route('/feedbackForm')
def feedbackForm():
    return render_template('feedbackForm.html')

@app.route('/about')
def about():
    return render_template('about.html')


def gen(camera, landmarked):
    while True:
        if landmarked == True:
            frame = camera.get_frame(True)
        else:
            frame = camera.get_frame(False)
        # yield (b'--frame\r\n'
        #        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        if frame is None:
            break
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/toggle_button', methods=['POST'])
def toggle_button():
    new_state, camera_state = button_toggle.toggle()
    if camera_state:
        print("Starting camera...")
        camera2.start_camera()  # Start the camera if the state is "Stop"
    else:
        print("Stopping camera...")
        camera2.stop_camera()  # Stop the camera if the state is "Start"
    return jsonify(state=new_state)

@app.route('/video_feed')
def video_feed():
    return Response(gen(camera2, False),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/landmarked_video')
def landmarked_video():
    return Response(gen(camera2, True),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/emotion_feed')
def emotion_feed():
    return jsonify(camera2.get_emotion_counts())

@app.route('/bored_feed')
def bored_feed():
    return jsonify(camera2.get_Bored_Counts())


# ----------------------------DB related
# check_connection: to test server connected to DB
# POST, GET all and GET by ID APIs

def check_connection():
    try:
        # Attempt to access a collection to check if the connection is successful
        db.list_collection_names()
        return True
    except Exception as e:
        print(f"Failed to connect to MongoDB: {str(e)}")
        return False
# Check MongoDB connection
if check_connection():
    print("Successfully connected to MongoDB.")
else:
    print("Failed to connect to MongoDB.")

# create a new entry for the movie in the DB
@app.route('/movies', methods=['POST'])
def add_movie():
    data = request.get_json()
    movie = {
        "title": data['title'],
        "description": data['description'],
        "release_date": data['release_date'],
        "genre": data['genre'],
        "DisplayGenre": data['DisplayGenre'],
        "FilmFile": data['FilmFile'],
        "Thumbnail": data['Thumbnail'],
        "movie_emotion_chart_id": ObjectId(data['movie_emotion_chart_id'])
    }
    result = db.movies.insert_one(movie)
    return jsonify({"_id": str(result.inserted_id)}), 201

# get all the movies stored in the DB
@app.route('/movies', methods=['GET'])
def get_movies():
    movies = list(db.movies.find())
    for movie in movies:
        movie['_id'] = str(movie['_id'])
        movie['movie_emotion_chart_id'] = str(movie['movie_emotion_chart_id'])
    return jsonify(movies), 200

# get one movie that matches the provided ID from DB
@app.route('/movies/<movie_id>', methods=['GET'])
def get_movie(movie_id):
    movie = db.movies.find_one({"_id": ObjectId(movie_id)})
    if movie:
        movie['_id'] = str(movie['_id'])
        movie['movie_emotion_chart_id'] = str(movie['movie_emotion_chart_id'])
        return jsonify(movie), 200
    else:
        return jsonify({"error": "Movie not found"}), 404

@app.route('/movie_details/<movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    movie = db.movies.find_one({"_id": ObjectId(movie_id)})
    if movie:
        movie['_id'] = str(movie['_id'])
        movie['movie_emotion_chart_id'] = str(movie['movie_emotion_chart_id'])
        # aggregate with the emotion chart data
        movie['emotion_chart'] = db.emotion_charts.find_one({"_id": ObjectId(movie['movie_emotion_chart_id'])})
        if movie['emotion_chart']:
            movie['emotion_chart']['_id'] = str(movie['emotion_chart']['_id'])
            return jsonify(movie), 200
        else:
            return jsonify({"error": "Emotion chart not found"}), 404
    else:
        return jsonify({"error": "Movie not found"}), 404

@app.route('/emotion_charts', methods=['POST'])
def add_emotion_chart():
    data = request.get_json()
    emotion_chart = {
        "angry": data['angry'],
        "disgust": data['disgust'],
        "fear": data['fear'],
        "happy": data['happy'],
        "sad": data['sad'],
        "surprise": data['surprise']
    }
    result = db.emotion_charts.insert_one(emotion_chart)
    return jsonify({"_id": str(result.inserted_id)}), 201
@app.route('/emotion_charts', methods=['GET'])
def get_emotion_charts():
    emotion_charts = list(db.emotion_charts.find())
    for emotion_chart in emotion_charts:
        emotion_chart['_id'] = str(emotion_chart['_id'])
    return jsonify(emotion_charts), 200

@app.route('/emotion_charts/<emotion_chart_id>', methods=['GET'])
def get_emotion_chart(emotion_chart_id):
    emotion_chart = db.emotion_charts.find_one({"_id": ObjectId(emotion_chart_id)})
    if emotion_chart:
        emotion_chart['_id'] = str(emotion_chart['_id'])
        return jsonify(emotion_chart), 200
    else:
        return jsonify({"error": "Emotion chart not found"}), 404
# change a emotion chart to update it with the user recording.
@app.route('/emotion_charts/<emotion_chart_id>', methods=['PUT'])
def update_emotion_chart(emotion_chart_id):
    data = request.get_json()
    updated_emotion_chart = {
        "angry": data.get('angry'),
        "disgust": data.get('disgust'),
        "fear": data.get('fear'),
        "happy": data.get('happy'),
        "sad": data.get('sad'),
        "surprise": data.get('surprise')
    }
    # find the element you want to change based on the ID
    result = db.emotion_charts.update_one(
        {"_id": ObjectId(emotion_chart_id)},
        {"$set": updated_emotion_chart}
    )
    if result.matched_count > 0:
        return jsonify({"message": "Emotion chart updated successfully"}), 200
    else:
        return jsonify({"error": "Emotion chart not found"}), 404

@app.route('/recording_emotions', methods=['POST'])
def add_recording_emotion():
    data = request.get_json();
    recording_emotion = {
        "movie_id": ObjectId(data['movie_id']),
        "start_time": datetime.strptime(data['start_time'], "%Y-%m-%dT%H:%M:%S"),
        "end_time": datetime.strptime(data['end_time'], "%Y-%m-%dT%H:%M:%S"),
        "emotion_chart_id": ObjectId(data['emotion_chart_id'])
    }
    result = db.recording_emotions.insert_one(recording_emotion)
    return jsonify({"_id": str(result.inserted_id)}), 201

@app.route('/recording_emotions', methods=['GET'])
def get_recording_emotions():
    recording_emotions = list(db.recording_emotions.find())
    for recording_emotion in recording_emotions:
        recording_emotion['_id'] = str(recording_emotion['_id'])
        recording_emotion['movie_id'] = str(recording_emotion['movie_id'])
        recording_emotion['emotion_chart_id'] = str(recording_emotion['emotion_chart_id'])
    return jsonify(recording_emotions), 200

@app.route('/recording_emotions/<recording_emotion_id>', methods=['GET'])
def get_recording_emotion(recording_emotion_id):
    recording_emotion = db.recording_emotions.find_one({"_id": ObjectId(recording_emotion_id)})
    if recording_emotion:
        recording_emotion['_id'] = str(recording_emotion['_id'])
        recording_emotion['movie_id'] = str(recording_emotion['movie_id'])
        recording_emotion['emotion_chart_id'] = str(recording_emotion['emotion_chart_id'])
        return jsonify(recording_emotion), 200
    else:
        return jsonify({"error": "Recording emotion not found"}), 404

@app.route('/movie_emotion_charts', methods=['POST'])
def add_movie_emotion_chart():
    data = request.get_json()
    movie_emotion_chart = {
        "emotion_chart_id": ObjectId(data['emotion_chart_id'])
    }
    result = db.movie_emotion_charts.insert_one(movie_emotion_chart)
    return jsonify({"_id": str(result.inserted_id)}), 201

@app.route('/movie_emotion_charts', methods=['GET'])
def get_movie_emotion_charts():
    movie_emotion_charts = list(db.movie_emotion_charts.find())
    for movie_emotion_chart in movie_emotion_charts:
        movie_emotion_chart['_id'] = str(movie_emotion_chart['_id'])
        movie_emotion_chart['emotion_chart_id'] = str(movie_emotion_chart['emotion_chart_id'])
    return jsonify(movie_emotion_charts), 200

@app.route('/movie_emotion_charts/<movie_emotion_chart_id>', methods=['GET'])
def get_movie_emotion_chart(movie_emotion_chart_id):
    movie_emotion_chart = db.movie_emotion_charts.find_one({"_id": ObjectId(movie_emotion_chart_id)})
    if movie_emotion_chart:
        movie_emotion_chart['_id'] = str(movie_emotion_chart['_id'])
        movie_emotion_chart['emotion_chart_id'] = str(movie_emotion_chart['emotion_chart_id'])
        return jsonify(movie_emotion_chart), 200
    else:
        return jsonify({"error": "Movie emotion chart not found"}), 404

@app.route('/addCameraEmotions', methods=['POST'])
def addCameraEmotions():
    # print("addCameraEmotions")
    data = request.get_json()
    movieID = data['movie_id']
    # print("movieID", movieID)
    # create a new emotion chart
    emotionData = camera2.get_emotion_counts()
    boredData=camera2.get_Bored_Counts()
    boredCount=boredData["Boredom"]
    emotion_chart = {
        "angry": emotionData['Angry']/100,
        "disgust": emotionData['Disgust']/100,
        "fear": emotionData['Fear']/100,
        "happy": emotionData['Happy']/100,
        "sad": emotionData['Sad']/100,
        "surprise": emotionData['Surprise']/100,
        "boredCount": boredCount,
    }
    result_emotion_chart = db.emotion_charts.insert_one(emotion_chart)
    emotion_chart_id = str(result_emotion_chart.inserted_id)
    # print("new emotion chart added", emotion_chart_id)

    # add a new recording for this movie
    # Check for start_time and end_time in data
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')
    # Convert start_time and end_time if provided, else set to None
    start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S") if start_time_str else None
    end_time = datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M:%S") if end_time_str else None

    recording_emotion = {
        "movie_id": ObjectId(movieID),
        "start_time": start_time,
        "end_time": end_time,
        "emotion_chart_id": ObjectId(emotion_chart_id)
    }
    db.recording_emotions.insert_one(recording_emotion)
    # print("new recording_emotions added")
    # get the main emotion chart of the movie and update with the new values

    # get how many recording are for a movie
    recording_emotions = list(db.recording_emotions.find({"movie_id": ObjectId(movieID)}))
    total_entries = len(recording_emotions)-1 # subtract the new one added
    # print("total recordings for this movie:", total_entries)
    # get the movie emotion chart
    movie = db.movies.find_one({"_id": ObjectId(movieID)})
    movie_emotion_chart_id = str(movie['movie_emotion_chart_id'])
    # print("main movie_emotion_chart_id", movie_emotion_chart_id)
    # get the emotion_chart of the movie with all the aggregated data and update the chart with the new values
    movie_emotion_chart = db.emotion_charts.find_one({"_id": ObjectId(movie_emotion_chart_id)})
    # print("main emotion_chart", movie_emotion_chart)
    if movie_emotion_chart:
        movie_emotion_chart['_id'] = str(movie_emotion_chart['_id'])
        # print("merge with new emotion chart")
        # print(emotion_chart)
        # Check if 'boredCount' exists in movie_emotion_chart
        oldBoredCount = 0
        if 'boredCount' in movie_emotion_chart:
            oldBoredCount = movie_emotion_chart['boredCount']

        updated_emotion_chart = {
            "angry": (movie_emotion_chart['angry']*total_entries + emotion_chart['angry'])/(total_entries+1),
            "disgust": (movie_emotion_chart['disgust']*total_entries + emotion_chart['disgust'])/(total_entries+1),
            "fear": (movie_emotion_chart['fear']*total_entries + emotion_chart['fear'])/(total_entries+1),
            "happy": (movie_emotion_chart['happy']*total_entries + emotion_chart['happy'])/(total_entries+1),
            "sad": (movie_emotion_chart['sad']*total_entries + emotion_chart['sad'])/(total_entries+1),
            "surprise": (movie_emotion_chart['surprise']*total_entries + emotion_chart['surprise'])/(total_entries+1),
            "boredCount": (oldBoredCount*total_entries + emotion_chart['boredCount'])/(total_entries+1)
        }
        # print("update chart values:")
        # print(updated_emotion_chart)

        # find the element you want to change based on the ID
        chart_update_result = db.emotion_charts.update_one(
            {"_id": ObjectId(movie_emotion_chart['_id'])},
            {"$set": updated_emotion_chart}
        )
        # print("update emotion chart")
        # print(chart_update_result)
        # Check if the update was successful
        if chart_update_result.modified_count > 0:
            # Fetch the updated emotion chart document
            updated_chart = db.emotion_charts.find_one({"_id": ObjectId(movie_emotion_chart['_id'])})
            updated_chart['_id'] = str(updated_chart['_id'])  # Convert ObjectId to string
            updated_chart['emotion_chart_id'] = emotion_chart_id
            return jsonify(updated_chart), 200
        else:
            return jsonify({"error": "Emotion chart could not be updated"}), 404
    else:
        return jsonify({"error": "Emotion chart not found"}), 404

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    # PANAS question mapping
    # panas_mapping = {
    #     "panas1": "Interested",
    #     "panas2": "Distressed",
    #     "panas3": "Excited",
    #     "panas4": "Upset",
    #     "panas5": "Strong",
    #     "panas6": "Guilty",
    #     "panas7": "Scared",
    #     "panas8": "Hostile",
    #     "panas9": "Enthusiastic",
    #     "panas10": "Proud",
    #     "panas11": "Irritable",
    #     "panas12": "Alert",
    #     "panas13": "Ashamed",
    #     "panas14": "Inspired",
    #     "panas15": "Nervous",
    #     "panas16": "Determined",
    #     "panas17": "Attentive",
    #     "panas18": "Jittery",
    #     "panas19": "Active",
    #     "panas20": "Afraid"
    # }
    # Extract data from the POST request
    # panas_responses = {}
    # for form_key, mapped_key in panas_mapping.items():
    #     panas_response = request.form.get(form_key)
    #     panas_responses[mapped_key] = panas_response

    website_questionnaire = {
        'q1': request.form.get('q1'),
        'q2': request.form.get('q2'),
        'q3': request.form.get('q3'),
        'q4': request.form.get('q4'),
        'q5': request.form.get('q5')
    }

    sus_responses = {
        "sus1": request.form.get('sus1'),
        "sus2": request.form.get('sus2'),
        "sus3": request.form.get('sus3'),
        "sus4": request.form.get('sus4'),
        "sus5": request.form.get('sus5'),
        "sus6": request.form.get('sus6'),
        "sus7": request.form.get('sus7'),
        "sus8": request.form.get('sus8'),
        "sus9": request.form.get('sus9'),
        "sus10": request.form.get('sus10'),
        "sus11": request.form.get('sus11')
    }

    emotion_responses = {
        "angry": request.form.get('emotion1'),
        "disgust": request.form.get('emotion2'),
        "fear": request.form.get('emotion3'),
        "happy": request.form.get('emotion4'),
        "sad": request.form.get('emotion5'),
        "surprise": request.form.get('emotion6'),
        "bored": request.form.get('emotion7')
    }
    formId=request.form.get('formId')

    # Prepare feedback document to insert into MongoDB
    feedback_doc = {
        'website_questionnaire': website_questionnaire,
        # 'panas_questionnaire': panas_responses,
        'emotional_response': emotion_responses,
        'sus_responses': sus_responses,
        "emotionChartId":formId,
    }

    # Insert feedback document into MongoDB
    result = db.feedback.insert_one(feedback_doc)

    # Get the inserted document's ID
    feedback_id = str(result.inserted_id)

    # Redirect to thank you page after successful submission
    return redirect(url_for('thank_you', feedback_id=feedback_id))


@app.route('/feedback', methods=['GET'])
def get_feedback():
    feedback_charts = list(db.feedback.find())
    mixed_data = []

    for feedback_chart in feedback_charts:
        feedback_chart['_id'] = str(feedback_chart['_id'])

        # Get emotionChartId from feedback_chart
        emotion_chart_id = feedback_chart.get('emotionChartId')
        print(emotion_chart_id)
        if emotion_chart_id:
            # Retrieve emotion_chart data based on emotionChartId
            emotion_chart = db.emotion_charts.find_one({'_id': ObjectId(emotion_chart_id)})
            if emotion_chart:
                emotion_chart['_id'] = str(emotion_chart['_id'])
                # Merge feedback_chart and emotion_chart data
                mixed_data.append({
                    'feedback_chart': feedback_chart,
                    'emotion_chart': emotion_chart,
                })
            else:
                # If emotion_chart with given _id not found, handle as needed
                mixed_data.append({
                    'feedback_chart': feedback_chart,
                    'emotion_chart': None  # or handle error condition
                })
        else:
            # Handle case where emotionChartId is not present in feedback_chart
            mixed_data.append({
                'feedback_chart': feedback_chart,
                'emotion_chart': None  # or handle error condition
            })
    return jsonify(mixed_data), 200

# Route for the thank you page
@app.route('/thank_you/<feedback_id>')
def thank_you(feedback_id):
    return render_template('thank_you.html', feedback_id=feedback_id)


if __name__ == '__main__':
    app.run(debug=True)
