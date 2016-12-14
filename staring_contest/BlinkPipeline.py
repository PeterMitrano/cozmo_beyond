import cv2
import numpy
import math
from enum import Enum

class Pipeline:
    """This is a generated class from GRIP.
    To use the pipeline first create a improved_pipeline instance and set the sources,
    next call the process method,
    finally get and use the outputs.
    """
    
    def __init__(self):
        """initializes all values to presets or None if need to be set
        """
        self.__lastImage0 = numpy.ndarray([])
        self.__source0 = None

        self.threshold_moving_output = None

        self.__blur_input = self.threshold_moving_output
        self.__blur_type = BlurType.Box_Blur
        self.__blur_radius = 6
        self.blur_output = None

        self.__cv_threshold_src = self.blur_output
        self.__cv_threshold_thresh = 12.0
        self.__cv_threshold_maxval = 255.0
        self.__cv_threshold_type = cv2.THRESH_BINARY
        self.cv_threshold_output = None

        self.__cv_adaptivethreshold_src = self.cv_threshold_output
        self.__cv_adaptivethreshold_maxvalue = 255.0
        self.__cv_adaptivethreshold_adaptivemethod = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        self.__cv_adaptivethreshold_thresholdtype = cv2.THRESH_BINARY
        self.__cv_adaptivethreshold_blocksize = 127.0
        self.__cv_adaptivethreshold_c = 0.0
        self.cv_adaptivethreshold_output = None

        self.__find_blobs_input = self.cv_adaptivethreshold_output
        self.__find_blobs_min_area = 56.0
        self.__find_blobs_circularity = [0.0, 1.0]
        self.__find_blobs_dark_blobs = False
        self.find_blobs_output = None

    
    def process(self):
        """Runs the pipeline.
        Sets outputs to new values.
        Requires all sources to be set.
        """
        #Step Threshold_Moving0:
        self.__threshold_moving_image = self.__source0
        (self.__lastImage0, self.threshold_moving_output ) = self.__threshold_moving(self.__threshold_moving_image, self.__lastImage0)

        #Step Blur0:
        self.__blur_input = self.threshold_moving_output
        (self.blur_output ) = self.__blur(self.__blur_input, self.__blur_type, self.__blur_radius)

        #Step CV_Threshold0:
        self.__cv_threshold_src = self.blur_output
        (self.cv_threshold_output ) = self.__cv_threshold(self.__cv_threshold_src, self.__cv_threshold_thresh, self.__cv_threshold_maxval, self.__cv_threshold_type)

        #Step CV_adaptiveThreshold0:
        self.__cv_adaptivethreshold_src = self.cv_threshold_output
        (self.cv_adaptivethreshold_output ) = self.__cv_adaptivethreshold(self.__cv_adaptivethreshold_src, self.__cv_adaptivethreshold_maxvalue, self.__cv_adaptivethreshold_adaptivemethod, self.__cv_adaptivethreshold_thresholdtype, self.__cv_adaptivethreshold_blocksize, self.__cv_adaptivethreshold_c)

        #Step Find_Blobs0:
        self.__find_blobs_input = self.cv_adaptivethreshold_output
        (self.find_blobs_output ) = self.__find_blobs(self.__find_blobs_input, self.__find_blobs_min_area, self.__find_blobs_circularity, self.__find_blobs_dark_blobs)

    def set_source0(self, value):
        """Sets source0 to given value checking for correct type.
        """
        assert isinstance(value, numpy.ndarray) , "Source must be of type numpy.ndarray"
        self.__source0 = value
    


    @staticmethod
    def __threshold_moving(input, last_image):
        """Thresholds off parts of the image that have moved or changed between
           the previous and next image.
        Args:
            input: A numpy.ndarray.
            last_image: The previous value of the numpy.ndarray.
        Returns:
            A numpy.ndarray with the parts that are the same in black.
        """
        if (last_image.shape == input.shape):
            output =  cv2.absdiff(input, last_image)
        else:
            output = numpy.ndarray(shape=input.shape, dtype=input.dtype)
        return input, output

    @staticmethod
    def __blur(src, type, radius):
        """Softens an image using one of several filters.
        Args:
            src: The source mat (numpy.ndarray).
            type: The blurType to perform represented as an int.
            radius: The radius for the blur as a float.
        Returns:
            A numpy.ndarray that has been blurred.
        """
        if(type is BlurType.Box_Blur):
            ksize = int(2 * round(radius) + 1)
            return cv2.blur(src, (ksize, ksize))
        elif(type is BlurType.Gaussian_Blur):
            ksize = int(6 * round(radius) + 1)
            return cv2.GaussianBlur(src, (ksize, ksize), round(radius))
        elif(type is BlurType.Median_Filter):
            ksize = int(2 * round(radius) + 1)
            return cv2.medianBlur(src, ksize)
        else:
            return cv2.bilateralFilter(src, -1, round(radius), round(radius))

    @staticmethod
    def __cv_threshold(src, thresh, max_val, type):
        """Apply a fixed-level threshold to each array element in an image
        Args:
            src: A numpy.ndarray.
            thresh: Threshold value.
            max_val: Maximum value for THRES_BINARY and THRES_BINARY_INV.
            type: Opencv enum.
        Returns:
            A black and white numpy.ndarray.
        """
        return cv2.threshold(src, thresh, max_val, type)[1]

    @staticmethod
    def __cv_adaptivethreshold(src, max_value, adaptive_method, threshold_type, block_size, c):
        """Applies an adaptive threshold to an array.
        Args:
            src: A gray scale numpy.ndarray.
            max_value: Value to assign to pixels that match the condition.
            adaptive_method: Adaptive threshold method to use. (opencv enum)
            threshold_type: Type of threshold to use. (opencv enum)
            block_size: Size of a pixel area that is used to calculate a threshold.(number)
            c: Constant to subtract from the mean.(number)
        Returns:
            A black and white numpy.ndarray.
        """
        return cv2.adaptiveThreshold(src, max_value, adaptive_method, threshold_type,
                        (int)(block_size + 0.5), c)

    @staticmethod
    def __find_blobs(input, min_area, circularity, dark_blobs):
        """Detects groups of pixels in an image.
        Args:
            input: A numpy.ndarray.
            min_area: The minimum blob size to be found.
            circularity: The min and max circularity as a list of two numbers.
            dark_blobs: A boolean. If true looks for black. Otherwise it looks for white.
        Returns:
            A list of KeyPoint.
        """
        params = cv2.SimpleBlobDetector_Params()
        params.filterByColor = 1
        params.blobColor = (0 if dark_blobs else 255)
        params.minThreshold = 10
        params.maxThreshold = 220
        params.filterByArea = True
        params.minArea = min_area
        params.filterByCircularity = True
        params.minCircularity = circularity[0]
        params.maxCircularity = circularity[1]
        params.filterByConvexity = False
        params.filterByInertia = False
        detector = cv2.SimpleBlobDetector_create(params)
        return detector.detect(input)


BlurType = Enum('BlurType', 'Box_Blur Gaussian_Blur Median_Filter Bilateral_Filter')

