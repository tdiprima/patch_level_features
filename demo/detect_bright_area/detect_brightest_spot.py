# Finding the Brightest Spot in an Image using Python and OpenCV
# https://www.pyimagesearch.com/2014/09/29/finding-brightest-spot-image-using-python-opencv/
# Code MODIFIED by me.

# USAGE
# python bright.py --image images/retina.png --radius 41
# python bright.py --image images/retina-noise.png --radius 41
# python bright.py --image images/moon.png --radius 61

# import the necessary packages
import argparse
import cv2
import sys


def susceptible_method(grayscale_img, orig_image):
    """
    Finds 1 pixel having largest intensity value.
    Performs a naive attempt to find the (x, y) coordinates of
    the area of the image with the largest intensity value.
    :param grayscale_img:
    :param orig_image:
    :return:
    """
    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(grayscale_img)

    print("smallest pixel intensity value: ", minVal)
    print("largest pixel intensity value: ", maxVal)
    print("(x, y) coordinates of minVal: ", minLoc)
    print("(x, y) coordinates of maxLoc: ", maxLoc)

    # Draw a circle around the maxLoc
    cv2.circle(orig_image, maxLoc, 5, (255, 0, 0), 2)

    # display the results of the naive attempt
    cv2.imshow("Naive", orig_image)

    # imshow() only works with waitKey():
    # https://stackoverflow.com/questions/21810452/cv2-imshow-command-doesnt-work-properly-in-opencv-python
    cv2.waitKey(0)


def more_robust_method(grayscale_img, orig_image):
    """
    Shows ROI; not just 1 pixel having highest intensity.
    Applies a Gaussian blur to the image then finds the brightest region.
    :param grayscale_img:
    :param orig_image:
    :return:
    """
    gray1 = cv2.GaussianBlur(grayscale_img, (args["radius"], args["radius"]), 0)

    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(gray1)
    print("smallest pixel intensity value: ", minVal)
    print("largest pixel intensity value: ", maxVal)
    print("(x, y) coordinates of minVal: ", minLoc)
    print("(x, y) coordinates of maxLoc: ", maxLoc)

    image1 = orig_image.copy()
    cv2.circle(image1, maxLoc, args["radius"], (255, 0, 0), 2)

    # display the results of our newly improved method
    cv2.imshow("Robust", image1)
    cv2.waitKey(0)


if not len(sys.argv) > 1:
    print("USAGE:")
    print("python bright.py --image images/retina.png --radius 41")
    exit(1)

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", help="path to the image file")
ap.add_argument("-r", "--radius", type=int,
                help="radius of Gaussian blur; must be odd")
args = vars(ap.parse_args())

# load the image and convert it to grayscale
image = cv2.imread(args["image"])
orig = image.copy()  # save it for later
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# susceptible_method(gray, image)

more_robust_method(gray, orig)
