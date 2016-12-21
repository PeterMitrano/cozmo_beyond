#!python3

import os
import sys
import cv2
import pickle

if __name__ == "__main__":
    if not os.path.exists('data'):
        sys.exit("data directory does not exist")

    blink_dir = {'size': 0, 'data': []}
    last_response = ''
    for i in range(1000):
        filename = 'data/frame_' + str(i) + '.png'
        print(filename)
        data = cv2.imread(filename)
        cv2.imshow('data', data)
        cv2.waitKey(2)
        is_blink = input('?: ')
        if is_blink == '':
            is_blink = last_response
        blink_dir['data'].append(is_blink)
        blink_dir['size'] = i + 1
        last_response = is_blink

        f = open("labels.pkl", 'wb')
        pickle.dump(blink_dir, f)
    cv2.destroyAllWindows()
