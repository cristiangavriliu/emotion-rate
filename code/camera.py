import cv2
import dlib
from scipy.spatial import distance
from tensorflow.keras.models import load_model
import numpy as np
from tensorflow.keras.preprocessing.image import img_to_array
import threading
from time import sleep

class VideoCamera(object):
    emotion_counts = {'Angry': 0, 'Disgust': 0, 'Fear': 0, 'Happy': 0, 'Neutral': 0, 'Sad': 0, 'Surprise': 0}
    bored_counts = {'TiredEyes': 0, 'Yawns': 0, 'Boredom': 0}
    emotion = 0
    frontal_face_detector = dlib.get_frontal_face_detector()
    dlib_facelandmark = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    tired_eyes = False
    blinking_eyes = False
    active_eyes = True
    previous_eye_aspect_ratio = 0.0
    current_eye_aspect_ratio = 0
    isTired_Eyes = False
    isTired_Yawn = False
    current_yawn_detected = False
    previous_yawn_detected = False
    yawn_counter_frames = 0
    yawn_counter = 0
    yawn_threshold = 3
    isYawning = False
    isBored = False


    def __init__(self):
        self.video = None
        self.camera_on = False
        self.face_classifier = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        self.classifier = load_model('Model/model.h5', compile=False)
        self.emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']
        self.frame = None
        self.lock = threading.Lock()
        self.emotion_thread = None
        self.emotion_thread_stop_event = threading.Event()
        self.bored_thread = None
        self.bored_thread_stop_event = threading.Event()

    def __del__(self):
        if self.video is not None:
            self.video.release()

    def calculate_Eye_Aspect_Ratio(self, eye):
        distance1 = distance.euclidean(eye[1], eye[5])
        distance2 = distance.euclidean(eye[2], eye[4])
        distance3 = distance.euclidean(eye[0], eye[3])
        eye_aspect_ratio = (distance1 + distance2) / (2.0 * distance3)
        return eye_aspect_ratio

    def calculateEyes(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.frontal_face_detector(gray)

        for face in faces:
            face_landmarks = self.dlib_facelandmark(gray, face)
            leftEye = []
            rightEye = []

            #dlib face landmark 36 to 41: left eye (Right outer corner of the eye, etc.)
            for n in range(36, 42):
                x = face_landmarks.part(n).x
                y = face_landmarks.part(n).y
                leftEye.append((x, y))

            #dlib face landmark 42 to 47: right eye (Left outer corner of the eye, etc.)
            for n in range(42, 48):
                x = face_landmarks.part(n).x
                y = face_landmarks.part(n).y
                rightEye.append((x, y))
                
                
                

            left_eye_aspect_ratio = self.calculate_Eye_Aspect_Ratio(leftEye)
            right_eye_aspect_ratio = self.calculate_Eye_Aspect_Ratio(rightEye)

            self.previous_eye_aspect_ratio = self.current_eye_aspect_ratio
            self.current_eye_aspect_ratio = (left_eye_aspect_ratio + right_eye_aspect_ratio) / 2

            if self.current_eye_aspect_ratio < 0.26:
                if self.previous_eye_aspect_ratio < 0.26:
                    self.tired_eyes = True
                    self.blinking_eyes = False
                    self.active_eyes = False
                    self.isTired_Eyes = True
                    self.bored_counts['TiredEyes'] +=1
                    
                else:
                    self.tired_eyes = False
                    self.blinking_eyes = True
                    self.active_eyes = False
                    self.isTired_Eyes = False
            else:
                self.tired_eyes = False
                self.blinking_eyes = False
                self.active_eyes = True
                self.isTired_Eyes = False


    def get_frame(self, landmarkedVideo):
        if not self.camera_on or self.video is None:
            print("Error: Camera is off or video is not initialized")
            return None
        ret, frame = self.video.read()

        if not ret or frame is None:
            print("Error: Frame is empty or could not be read")
            return None

        if self.camera_on:
            with self.lock:
                self.frame = frame.copy()
                frame_Copy = frame.copy()

            if landmarkedVideo == True:
                self.mark_landmarks(frame_Copy)

            # Gesichtserkennung hinzufügen und Rechteck zeichnen
            gray = cv2.cvtColor(frame_Copy, cv2.COLOR_BGR2GRAY)
            faces = self.face_classifier.detectMultiScale(gray)

            if len(faces) >0:
                x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
                if w >= 30 and h >= 30 and 0.8 <= w / h <= 1.2:
                    cv2.rectangle(frame_Copy, (x, y), (x + w, y + h), (0, 255, 255), 2)
                    roi_gray = gray[y:y + h, x:x + w]
                    roi_gray = cv2.resize(roi_gray, (48, 48), interpolation=cv2.INTER_AREA)


                if np.sum([roi_gray]) != 0:
                    roi = roi_gray.astype('float') / 255.0
                    roi = img_to_array(roi)
                    roi = np.expand_dims(roi, axis=0)

                    prediction = self.classifier.predict(roi)[0]
                    label = self.emotion_labels[prediction.argmax()]

                    self.emotion_counts[label] += 1
                    label_position = (x, y - 10)
                    cv2.putText(frame_Copy, label, label_position, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    cv2.putText(frame_Copy, 'Face not detected', (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)


        ret, jpeg = cv2.imencode('.jpg', frame_Copy)
        if not ret:
            print("Error: Could not encode frame to JPEG")
            return None
        return jpeg.tobytes()

    def start_camera(self):
        if not self.camera_on:
            self.camera_on = True
            self.video = cv2.VideoCapture(0)
            #self.video.set(cv2.CAP_PROP_FPS, 5)
            if not self.video.isOpened():
                print("Error: Could not open video device")
                self.camera_on = False
                return

            # Start the emotion detection thread
            self.emotion_thread_stop_event.clear()
            self.emotion_thread = threading.Thread(target=self.calculateEmotion, daemon=True)
            self.emotion_thread.start()

            print("Emotion Thread startet")

            # Starte den Thread für calculateEyes
            self.bored_thread_stop_event.clear()
            self.bored_thread = threading.Thread(target=self.bored_threaded, daemon=True)
            self.bored_thread.start()

            print("Bored Thread started")
 

    def bored_threaded(self):
        try:
            while not self.bored_thread_stop_event.is_set():
                if self.camera_on and self.frame is not None:
                    with self.lock:
                        frame = self.frame.copy()
                    self.calculateEyes(frame)
                    self.calculateYawn(frame)
        except Exception as e:
            print(f"Error in bored_threaded: {e}")
            traceback.print_exc()

    def stop_camera(self):
        if self.camera_on:
            self.camera_on = False
            if self.video is not None:
                self.video.release()
                self.video = None

            # Stop the emotion detection thread
            self.emotion_thread_stop_event.set()
            if self.emotion_thread is not None:
                self.emotion_thread.join()
                self.emotion_thread = None

            # Stoppe die Threads für calculateEyes und calculateYawn
            self.bored_thread_stop_event.set()
            if self.bored_thread is not None:
                self.bored_thread.join()
                self.bored_thread = None

    def calculateEmotion(self):
        while not self.emotion_thread_stop_event.is_set():
            if self.frame is None:
                continue
            with self.lock:
                frame = self.frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_classifier.detectMultiScale(gray)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
                roi_gray = gray[y:y + h, x:x + w]
                roi_gray = cv2.resize(roi_gray, (48, 48), interpolation=cv2.INTER_AREA)

                if np.sum([roi_gray]) != 0:
                    roi = roi_gray.astype('float') / 255.0
                    roi = img_to_array(roi)
                    roi = np.expand_dims(roi, axis=0)

                    prediction = self.classifier.predict(roi)[0]
                    label = self.emotion_labels[prediction.argmax()]

                    self.emotion_counts[label] += 1
                    label_position = (x, y - 10)
                    cv2.putText(frame, label, label_position, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, 'Face not detected', (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    def get_emotion_counts(self):
        total_counts = sum(count for emotion, count in self.emotion_counts.items() if emotion != 'Neutral')
        if total_counts == 0:
            return {emotion: 0 for emotion in self.emotion_counts if emotion != 'Neutral'}
        emotion_percentages = {emotion: (count / total_counts) * 100 for emotion, count in self.emotion_counts.items() if emotion != 'Neutral'}
        return emotion_percentages

    def extract_landmarks (self, frame):
        faces = self.frontal_face_detector(frame,1)
        if len(faces) > 1:
          return "error"
        if len(faces) == 0:
          return "error"
        return np.matrix([[p.x, p.y] for p in self.dlib_facelandmark(frame, faces[0]).parts()])


    def mark_landmarks(self, frame):

        with self.lock:
            faces_counter = self.frontal_face_detector(frame,1)
            if len(faces_counter) > 1:
                return "error"
            if len(faces_counter) == 0:
                return "error"

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.frontal_face_detector(gray)

            for face in faces:
                face_landmarks = self.dlib_facelandmark(gray, face)

                leftEye = []
                rightEye = []

                #dlib face landmark 36 to 41: left eye (Right outer corner of the eye, etc.)
                for n in range(36, 42):
                    x = face_landmarks.part(n).x
                    y = face_landmarks.part(n).y
                    leftEye.append((x, y))
                    next_landmark = n + 1
                    if n == 41:
                        next_landmark = 36
                    #draw a line from every eye face point to the next one
                    x2 = face_landmarks.part(next_landmark).x
                    y2 = face_landmarks.part(next_landmark).y
                    cv2.line(frame, (x, y), (x2, y2), (0, 255, 0), 1)

                #dlib face landmark 42 to 47: right eye (Left outer corner of the eye, etc.)
                for n in range(42, 48):
                    x = face_landmarks.part(n).x
                    y = face_landmarks.part(n).y
                    rightEye.append((x, y))
                    next_landmark = n + 1
                    if n == 47:
                        next_landmark = 42
                    #draw a line from every eye landmark to the next one
                    x2 = face_landmarks.part(next_landmark).x
                    y2 = face_landmarks.part(next_landmark).y
                    cv2.line(frame, (x, y), (x2, y2), (0, 255, 0), 1)

                # Landmarks for upper and lower lips
                upperLip_indices = [48, 49, 50, 51, 52, 53, 54, 64, 63, 62, 61, 60]
                lowerLip_indices = [60, 67, 66, 65, 54, 55, 56, 57, 58, 59, 48]

                # Draw lines for upper lip
                for i in range(len(upperLip_indices) - 1):
                    x1, y1 = face_landmarks.part(upperLip_indices[i]).x, face_landmarks.part(upperLip_indices[i]).y
                    x2, y2 = face_landmarks.part(upperLip_indices[i + 1]).x, face_landmarks.part(upperLip_indices[i + 1]).y
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)

                # Connect the last point to the first point to close the upper lip shape
                x1, y1 = face_landmarks.part(upperLip_indices[-1]).x, face_landmarks.part(upperLip_indices[-1]).y
                x2, y2 = face_landmarks.part(upperLip_indices[0]).x, face_landmarks.part(upperLip_indices[0]).y
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)

                for i in range(len(lowerLip_indices) - 1):
                    x1, y1 = face_landmarks.part(lowerLip_indices[i]).x, face_landmarks.part(lowerLip_indices[i]).y
                    x2, y2 = face_landmarks.part(lowerLip_indices[i + 1]).x, face_landmarks.part(lowerLip_indices[i + 1]).y
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)

                # Connect the last point to the first point to close the lower lip shape
                x1, y1 = face_landmarks.part(lowerLip_indices[-1]).x, face_landmarks.part(lowerLip_indices[-1]).y
                x2, y2 = face_landmarks.part(lowerLip_indices[0]).x, face_landmarks.part(lowerLip_indices[0]).y
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)

        


    def calculateYawn (self, frame):

       
        landmarks = self.extract_landmarks(frame)
        

        if isinstance(landmarks, str) and landmarks == "error":
            
            return
        


        #calculate upper lip and its center
        upper_lip_points = []
        for i in range(50, 53):
            upper_lip_points.append(landmarks[i])
        for i in range(61, 64):
            upper_lip_points.append(landmarks[i])
        upperLip = np.squeeze(np.asarray(upper_lip_points))
        upperLip_center_mean = np.mean(upper_lip_points, axis=0)
        upperLip_center = int(upperLip_center_mean[:,1])

        print("Oberlippe berechnet")

        #calculate lower lip and its center
        lower_lip_points = []
        for i in range(56, 59):
            lower_lip_points.append(landmarks[i])
        for i in range(65, 68):
            lower_lip_points.append(landmarks[i])
        lowerLip = np.squeeze(np.asarray(lower_lip_points))
        lowerLip_center_mean = np.mean(lower_lip_points, axis=0)
        lowerLip_center = int(lowerLip_center_mean[:,1])

        print("unterlippe berechnet")

        lip_distance = abs(upperLip_center - lowerLip_center)

        print(str(lip_distance))

        if lip_distance > 70: 
            self.current_yawn_detected = True
            print("counter yawns = " + str(self.yawn_counter_frames))
            if (self.yawn_counter_frames != 0):
                if (self.previous_yawn_detected == True):
                    self.yawn_counter_frames += 1
                else: 
                    self.yawn_counter_frames = 0
            else: 
                self.yawn_counter_frames +=1

            if (self.yawn_counter_frames >= self.yawn_threshold):
                self.isYawning = True
                self.isTired_Yawn = True

                if (self.tired_eyes == True and self.isTired_Yawn == True):
                    #cv2.putText(frame, "Müdigkeit entdeckt", (50, 450), cv2.FONT_HERSHEY_COMPLEX, 1,(0,0,255),2)
                    #output_text = "Yawn Count: " + str(self.yawn_counter + 1)
                    #cv2.putText(frame, output_text, (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0,255,127),2) 
                    self.isBored = True

        else: 
            self.current_yawn_detected = False
            self.isTired_Yawn = False

            if (self.isYawning and self.previous_yawn_detected == True and self.current_yawn_detected == False):
                self.isYawning = False
                self.yawn_counter +=1
                self.yawn_counter_frames = 0
                self.bored_counts['Yawns'] +=1
                if (self.isBored == True):
                    self.bored_counts['Boredom'] +=1
                self.isBored = False
                
                print("Aktuelle Zählerstände:")
                print(f"TiredEyes: {self.bored_counts['TiredEyes']}")
                print(f"Yawns: {self.bored_counts['Yawns']}")
                print(f"Boredom: {self.bored_counts['Boredom']}")
                
                sleep(3)

        self.previous_yawn_detected = self.current_yawn_detected


    def get_Bored_Counts(self):
        return self.bored_counts