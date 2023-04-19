"""
Detecting multiple bright spots in an image with Python and OpenCV
https://www.pyimagesearch.com/2016/10/31/detecting-multiple-bright-spots-in-an-image-with-python-and-opencv/
Code MODIFIED by me.
"""

from imutils import contours
from skimage import measure
import numpy as np
import argparse
import imutils
import cv2
import sys


def show_output(img):
    """
    Show the output image
    :param img:
    :return:
    """
    try:
        cv2.imshow("Image", img)
        cv2.waitKey(0)
    except cv2.error as err:
        print('\nCannot show the image.\n', err)
        exit(1)


def grayscale_and_blur(m_image):
    """
    Convert image to grayscale and blur it.
    :param m_image:
    :return:
    """
    gray = cv2.cvtColor(m_image, cv2.COLOR_BGR2GRAY)
    m_blurred = cv2.GaussianBlur(gray, (11, 11), 0)
    # show_img(m_blurred)
    return m_blurred


def reveal_brightest_regions(m_blurred):
    """
    Apply thresholding to reveal the brighter regions of the image.
    p >= 200 => 255 (white); p < 200 => 0 (black).
    :param m_blurred:
    :return:
    """
    m_thresh = cv2.threshold(m_blurred, 200, 255, cv2.THRESH_BINARY)[1]
    # show_img(m_thresh)
    return m_thresh


def clean_up_noise(m_thresh):
    """
    Remove small blobs and then regrow the remaining regions.
    :param m_thresh:
    :return:
    """
    m_thresh = cv2.erode(m_thresh, None, iterations=2)
    m_thresh = cv2.dilate(m_thresh, None, iterations=4)
    # show_img(m_thresh)
    return m_thresh


def clean_up_leftover_noise(m_thresh):
    """
    Apply connected-component analysis to get only the
    larger blobs in the image (which are also bright).
    :param m_thresh:
    :return:
    """
    labels = measure.label(m_thresh, neighbors=8, background=0)
    print("m_thresh.shape: ", m_thresh.shape)
    m_mask = np.zeros(m_thresh.shape, dtype="uint8")

    # loop over the unique components
    for label in np.unique(labels):
        # if this is the background label, ignore it
        if label == 0:
            continue

        # otherwise, construct the label mask and count the
        # number of pixels
        label_mask = np.zeros(m_thresh.shape, dtype="uint8")
        label_mask[labels == label] = 255
        num_pixels = cv2.countNonZero(label_mask)

        # if the number of pixels in the component is sufficiently
        # large, then add it to our mask of "large blobs"
        if num_pixels > 300:
            m_mask = cv2.add(m_mask, label_mask)

    return m_mask


def draw_labels(mask, m_image):
    """
    Find contours in mask, then sort from left to right.
    :param mask:
    :param m_image:
    :return:
    """
    counts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                              cv2.CHAIN_APPROX_SIMPLE)
    counts = counts[0] if imutils.is_cv2() else counts[1]
    counts = contours.sort_contours(counts)[0]

    # loop over the contours
    for (i, c) in enumerate(counts):
        # draw the bright spot on the image
        (x, y, w, h) = cv2.boundingRect(c)
        ((cX, cY), radius) = cv2.minEnclosingCircle(c)
        cv2.circle(m_image, (int(cX), int(cY)), int(radius),
                   (0, 0, 255), 3)
        cv2.putText(m_image, "#{}".format(i + 1), (x, y - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)

    return m_image


# start
if not len(sys.argv) > 1:
    program_name = sys.argv[0]
    print("USAGE:")
    print('python ', program_name, ' --image images/lights_01.png')
    exit(1)

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
                help="path to the image file")
args = vars(ap.parse_args())

image = cv2.imread(args["image"])

blurred = grayscale_and_blur(image)

thresh = reveal_brightest_regions(blurred)

thresh = clean_up_noise(thresh)

mask = clean_up_leftover_noise(thresh)

image = draw_labels(mask, image)

show_output(image)
