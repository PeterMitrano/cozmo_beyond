#!/usr/bin/python3

import cv2
import os
import tensorflow as tf

if __name__ == "__main__":
    cap = cv2.VideoCapture(0)

    # grab one frame in order to get dimensions
    camera_w = 480
    camera_h = 640

    # set up NN
    x = tf.placeholder(tf.float32, [None, camera_w * camera_h])
    W = tf.Variable(tf.zeros([camera_w * camera_h, 1]))
    b = tf.Variable(tf.zeros([1]))
    pred_y = tf.matmul(x, W) + b
    correct_y = tf.placeholder(tf.float32, [None, 1])
    binary_error = correct_y - pred_y
    train_step = tf.train.GradientDescentOptimizer(0.5).minimize(binary_error)

    init = tf.global_variables_initializer()
    sess = tf.Session()
    sess.run(init)

    # setup test/train data directory
    if not os.path.exists('data'):
        os.mkdir('data')

    for i in range(1000):
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        input_data = gray
        # correct_y_data = label
        # sess.run(train_step, feed_dict={x: input_data, correct_y: correct_y_data})

        cv2.imwrite('data/frame_' + str(i) + '.png', gray)

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()
