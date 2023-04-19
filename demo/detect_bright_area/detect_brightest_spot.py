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


def show_output(name, img):
    """
    Show the output image
    :param img:
    :return:
    """
    try:
        cv2.imshow(name, img)
        cv2.waitKey(0)
    except cv2.error as err:
        print('\nCannot show the image.\n', err)
        exit(1)


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
    show_output('Naive', orig_image)


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
    show_output('Robust', image1)


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", help="path to the image file")
ap.add_argument("-r", "--radius", type=int,
                help="radius of Gaussian blur; must be odd")
args = vars(ap.parse_args())
print(args)


if not len(sys.argv) > 1:
    program_name = sys.argv[0]
    print("USAGE:")
    print('python ', program_name, ' --image images/retina.png --radius 41')
    exit(1)

# load the image and convert it to grayscale
image = cv2.imread(args["image"])
orig = image.copy()  # save it for later
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# susceptible_method(gray, image)

more_robust_method(gray, orig)
