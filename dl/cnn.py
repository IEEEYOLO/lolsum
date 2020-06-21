from efficientnet.tfkeras  import EfficientNetB4
import cv2
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Dense, BatchNormalization, GlobalMaxPooling2D, Dropout
from tensorflow.keras.models import Sequential, load_model
from multiprocessing.pool import ThreadPool
from collections import deque
import matplotlib.pyplot as plt

class CNN():
    def __init__(self, input_path):
        self.predictions = dict()
        self.input_path = input_path

        self.num_thread = cv2.getNumberOfCPUs() * 8
        self.pool = ThreadPool(processes = self.num_thread)
        self.pending = deque()

        self.INTERVAL = 30
        self.model = load_model('../res/b4-aug.')

    def show_prediction(self, p):
        print(p)
    
    def predict_frame(self, frame, idx):
        frame = cv2.resize(frame, dsize=(600, 600))
        frame = np.reshape(frame, (1, 600, 600, 3))
        return idx, self.model.predict(frame)

    def predict_file(self, cap):
        frame_cnt = 0
        prediction = dict()

        while True:
            while len(self.pending) > 0 and self.pending[0].ready():
                print(self.pending.popleft().get())

            if len(self.pending) < self.num_thread:
                cap.set(1, frame_cnt)
                ret, frame = cap.read()
                frame_cnt += self.INTERVAL

                if ret:
                    task = self.pool.apply_async(self.predict_frame, (frame.copy(), frame_cnt//self.INTERVAL))
                    self.pending.append(task)
            
            if len(self.pending) == 0:
                cap.release()
                break

            if frame_cnt % 200 == 0:
                print("\r" + str(frame_cnt), end=" ")
                print(prediction)
        
        return list(prediction)

    def predict_file2(self, cap):
        frame_cnt = 0
        frames = []

        while True:
            cap.set(1, frame_cnt)
            ret, frame = cap.read()
            if not ret:
                break
            frame_cnt += self.INTERVAL
            frame = cv2.resize(frame, dsize=(600, 600))
            frames.append(frame)

            if frame_cnt % 200 == 0:
                print("\r" + str(frame_cnt), end=" ")
        
        frames = np.array(frames)
        prediction = self.model.predict(frames)
        psum = np.sum(prediction, axis=0)[1] / prediction.shape[0]
        return psum


    def predict(self):
        for filename in os.listdir(self.input_path):
            if not filename.endswith('.mp4'):
                continue
            print(filename)
            cap = cv2.VideoCapture(os.path.join(self.input_path, filename))
            psum = self.predict_file2(cap)
            self.predictions[filename] = psum

        return self.predictions


if __name__ == "__main__":
    cnn = CNN("C:\\Users\\SOGANG\\Downloads")
    print(cnn.predict())