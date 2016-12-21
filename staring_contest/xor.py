import random
import pickle
import sys
import os
import numpy as np
import tensorflow as tf

if __name__ == "__main__":
    # set up NN
    x = tf.placeholder(tf.float32, [1, 2])
    W = tf.Variable(tf.zeros([2, 1]))
    b = tf.Variable(tf.zeros([1]))
    pred_y = tf.matmul(x, W) + b
    correct_y = tf.placeholder(tf.float32, 1)
    binary_error = tf.nn.l2_loss(correct_y - pred_y)
    train_step = tf.train.GradientDescentOptimizer(0.5).minimize(binary_error)

    init = tf.global_variables_initializer()
    sess = tf.Session()
    sess.run(init)

    for i in range(5):

        # each batch is 100 examples of the XOR function
        a = random.randint(0, 1)
        b = random.randint(0, 1)
        batch_x = np.array([[a, b]])
        batch_y = np.array([a ^ b])

        # result = sess.run(x, feed_dict={x: [[1,0]]})
        # print(result)
        loss, acc = sess.run(train_step, feed_dict={x: batch_x, correct_y: batch_y})
        print("Iter " + str(i) + ", Minibatch Loss= " + \
              "{:.6f}".format(loss) + ", Training Accuracy= " + \
              "{:.5f}".format(acc))
