#!/usr/bin/python3

import cv2
import os
import tensorflow as tf

if __name__ == "__main__":
    cap = cv2.VideoCapture(0)

    # setup test/train data directory
    if not os.path.exists('data'):
        os.mkdir('data')

    for i in range(1000):
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imwrite('data/frame_' + str(i) + '.png', gray)

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()
