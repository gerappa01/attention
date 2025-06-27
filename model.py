import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import cv2
import time
import numpy as np
import mediapipe as mp
from collections import deque
import pandas as pd
from threading import Event
import scipy.signal as signal

mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
LEFT_EYE =  [362, 381, 384, 380, 385, 374, 386, 373, 387, 390, 388, 263]
RIGHT_EYE = [133, 157, 154, 158, 153, 159, 145, 160, 144, 161, 163,  33]
LEFT_PUPIL = [473]
RIGHT_PUPIL = [468]
NOSE = [4]
LANDMARK_IDS = list(set(LEFT_EYE + RIGHT_EYE + LEFT_PUPIL + RIGHT_PUPIL + NOSE))


from functools import wraps
def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.6f} seconds")
        return result
    return wrapper


class AttentionModel:
    def __init__(self, save_path="attn.csv", window_size=15*30, cap_visible=False):
        self.cap = cv2.VideoCapture(0)
        self.eye_points = None
        self.ear_threshold = 0.05
        self.landmarks_2d = None

        self.window_size = window_size

        # used for the pupil eye movements (is user reading)
        self.right_distances_window = deque(maxlen=self.window_size)
        self.FREQ_CUTOFF = 4 # no user will ever read 20 lines a second.

        # user detections
        self.user_is_looking_at_screen = 0
        self.user_is_blinking = 0
        self.user_is_reading = 0

        # attention (-1, 0, 1) list, timestamp list, ..., attention_scores_list (0.1103, 1.0, -0.8423, ...)
        self.attention_levels_list = []
        self.attention_timestamps_list = []
        self.user_is_looking_at_screen_list = []
        self.user_is_blinking_list = []
        self.user_is_reading_list = []
        self.attention_scores_list = []

        self.stop_event = Event()
        self.save_path = save_path

        self.cap_visible = cap_visible

    def is_user_blinking(self) -> None:
        """
        Takes upper eyelid point - lower eyelid point distances. If that is below self.ear_threshold -> True.
        Autoupdates self.user_is_blinking value.
        """
        verticals = [np.linalg.norm(self.eye_points[i] - self.eye_points[i + 1]) for i in range(1, 11, 2)]
        horizontal = np.linalg.norm(self.eye_points[0] - self.eye_points[-1])
        ear = sum(verticals) / (len(verticals) * horizontal)
        self.user_is_blinking = ear < self.ear_threshold
    
    def is_user_looking_at_screen(self) -> None:
        """
        Takes nose, inner-, outer-eye points. 
        if nose between inner points    -> 1
        elif nose between outer points  -> 0
        else                            -> -1
        Autoupdates self.user_is_looking_at_screen value.
        """
        nose_x = self.landmarks_2d[NOSE[0]][0]
        inner_left_x = self.landmarks_2d[LEFT_EYE[0]][0]
        inner_right_x = self.landmarks_2d[RIGHT_EYE[0]][0]
        outer_left_x = self.landmarks_2d[LEFT_EYE[-1]][0]
        outer_right_x = self.landmarks_2d[RIGHT_EYE[-1]][0]

        if inner_right_x < nose_x < inner_left_x:               # if   between inner
            self.user_is_looking_at_screen = 1
        elif outer_right_x < nose_x < outer_left_x:             # elif between outer
            self.user_is_looking_at_screen = 0
        else:                                                   # else
            self.user_is_looking_at_screen = -1
    
    def calculate_pupil_distance_from_inner_eye(self):
        """
        Calculates right pupil - inner eye point distance / horizontal eye aspect ratio.
        Updates self.right_distances_window deque by appending this AR.
        """           
        horizontal = np.linalg.norm(self.eye_points[0] - self.eye_points[-1])
        distance_from_inner_eye = np.linalg.norm(self.eye_points[0] - self.right_pupil_points[0])
        self.right_distances_window.append(distance_from_inner_eye / horizontal)
        
    def is_user_reading(self):
        """
        autoupdate object variable
        This is a math-heavy function. We have the rolling window of pupil-eye ratios.
        These values either follow a rhythmic sawtooth pattern, or they do not.
        They may also stop moving entirely, stationary.
        The presence of rhythmic sawtooth means reading, the presence of stationary values mean boredom.
        Lack of either does not imply presence of opposite.
        """
        def butter_lowpass_filter(data, cutoff, fs=30, order=4):
            nyquist = 0.5 * fs
            norm_cutoff = cutoff / nyquist
            b, a = signal.butter(order, norm_cutoff, btype='low', analog=False)
            return signal.filtfilt(b, a, data)

        def frequency_detection(filtered, fs=30):                 
            if len(filtered) < self.window_size:
                return None, None, None

            data = np.array(filtered)
            windowed = data * np.hamming(len(data))
            fft_result = np.abs(np.fft.rfft(windowed))
            freqs = np.fft.rfftfreq(len(windowed), d=1/fs)

            # Limit to cutoff
            cutoff_idx = np.where(freqs <= self.FREQ_CUTOFF)[0][-1]
            freqs = freqs[:cutoff_idx + 1]
            fft_result = fft_result[:cutoff_idx + 1]

            peak_idx = np.argmax(fft_result)
            peak_freq = freqs[peak_idx]
            peak_ampl = fft_result[peak_idx]

            return peak_freq, peak_ampl, fft_result

        # if user is not even looking at screen
        if self.user_is_looking_at_screen == -1:
            self.user_is_reading = -1
            return (0, 0)
        elif self.user_is_blinking:
            self.user_is_reading = 0
            return (0, 0)

        # Updating self.right_distances_window deque
        self.calculate_pupil_distance_from_inner_eye()
        
        # convert to nparray for faster calculations
        x = np.array(self.right_distances_window) 
        
        # buffer full check
        if len(self.right_distances_window) < self.right_distances_window.maxlen:
            self.user_is_reading = 0
            return (0, 0)
        
        # filter, detrend (remove DC)
        filtered = butter_lowpass_filter(x, cutoff=self.FREQ_CUTOFF)
        filtered_detrended = filtered - np.mean(filtered)

        peak_freq, peak_ampl, _ = frequency_detection(filtered_detrended)

        if 0.2 <= peak_freq < 3  and 0.5 <= peak_ampl:
            self.user_is_reading = 1
        elif 0 <= peak_freq < 4 and 0.3 <= peak_ampl:
            self.user_is_reading = 0
        else:
            self.user_is_reading = -1

        return peak_freq, peak_ampl
        
    def calculate_attention_score(self):
        """
        This is the scientifically important function in this entire pile of manure.
        The way attention score is calculated is the following:
            - we have a rolling window in which we are storing many values.
                - if the user is not looking at the screen at all (-1)                             -> 0       (ext. diverted attention)
                - if user is maybe looking at screen (0)                                           -> 1       (gray zone)
                - if user is def looking at screen (1):
                    - if user pupil moves similarly to the first two minutes of exp.               -> 2       (attentive)
                    - else                                                                         -> 0       (int. diverted attention)
            - we take the average of the current rolling window and return that value.
        """
        level = 0

        if len(self.right_distances_window) < self.right_distances_window.maxlen:
            level = 1
        elif self.user_is_looking_at_screen == -1 or self.user_is_reading == -1:
            level = -1
        elif self.user_is_reading == 0 or self.user_is_blinking:
            level = 0
        elif self.user_is_reading == 1:
            level = 1


        self.attention_levels_list.append(level)
        
        self.attention_timestamps_list.append(time.time())

        score = round(np.mean(self.attention_levels_list[-self.window_size:]), 4) # the attention window should be two times as big as the is_reading window
        
        self.user_is_looking_at_screen_list.append(self.user_is_looking_at_screen)
        self.user_is_blinking_list.append(self.user_is_blinking)
        self.user_is_reading_list.append(self.user_is_reading)
        self.attention_scores_list.append(score)

        # return score
        return score

    def save(self):
        self.cap.release()
        cv2.destroyAllWindows()
        df = pd.DataFrame({
                    'time': self.attention_timestamps_list,
                    'attention_levels': self.attention_levels_list,
                    'is_looking_at_screen_scores': self.user_is_looking_at_screen_list,
                    'is_blinking_scores': self.user_is_blinking_list,
                    'is_reading_scores': self.user_is_reading_list,
                    'attention_scores': self.attention_scores_list
                })
        df.to_csv(self.save_path)

    def measure(self):
        try:
            with mp_face_mesh.FaceMesh(max_num_faces=1,refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5) as face_mesh:
                while self.cap.isOpened() and not self.stop_event.is_set():
                    key = cv2.waitKey(1) & 0xFF
                    if key == 27:
                        break
                    ret, frame = self.cap.read()
                    if frame is None:
                        continue
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_mesh.process(frame_rgb)

                    if results.multi_face_landmarks:
                        for face_landmarks in results.multi_face_landmarks:
                            self.landmarks_2d = {i: np.array([face_landmarks.landmark[i].x,
                                        face_landmarks.landmark[i].y]) for i in LANDMARK_IDS}
                            self.eye_points = np.array([self.landmarks_2d[i] for i in LEFT_EYE + RIGHT_EYE])
                            self.right_pupil_points = np.array([self.landmarks_2d[i] for i in RIGHT_PUPIL])

                        self.is_user_looking_at_screen()
                        self.is_user_blinking()
                        peak_freq, peak_ampl = self.is_user_reading()
                        cv2.putText(frame, f'freq: {str(peak_freq)}', (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 1)
                        cv2.putText(frame, f'ampl: {str(peak_ampl)}', (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 1)

                        attention_level = self.calculate_attention_score()
                        cv2.putText(frame, f'looks: {str(self.user_is_looking_at_screen)}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
                        cv2.putText(frame, f'blinks: {str(self.user_is_blinking)}', (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        cv2.putText(frame, f'reads: {str(self.user_is_reading)}', (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                        if isinstance(attention_level, float):
                            cv2.putText(frame, f'attn: {str(round(attention_level, 3))}', (10, 210), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                        yield attention_level
                    
                    if self.cap_visible: cv2.imshow('Test attention detection', frame)
        
        except KeyboardInterrupt:
            print("AttentionModel measure: KeyboardInterrupt caught, cleaning up...")
            self.save()




if __name__ == "__main__":
    model = AttentionModel(cap_visible=True)
    for attn in model.measure():
        continue
    