import pickle
import sys
import os
import tensorflow as tf

if __name__ == "__main__":
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
        sys.exit('no data directory')

    input_data = pickle.load(open('labels.pkl', 'rb'))
    print(input_data['size'])

    for i in range(10000):
        batch_x = []
        batch_y = []
        for i in range(input_data['size']):
            batch_y[''] = input_data['data'][i]
        loss, acc = sess.run(train_step, feed_dict={x: batch_x, correct_y: batch_y})
        print("Iter " + str(i) + ", Minibatch Loss= " + \
              "{:.6f}".format(loss) + ", Training Accuracy= " + \
              "{:.5f}".format(acc))
        pass
