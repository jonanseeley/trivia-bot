# imports
from PIL import Image
from google import google
import pytesseract
import argparse
import cv2
import os
import re
import urllib2

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument('-i', '--image', required=True,
                help="path to input image to be OCR'd")
ap.add_argument('-p', '--preprocess', type=str, default='thresh',
                help="type or preprocessing to be done")
args = vars(ap.parse_args())

# load the example image and convert it to grayscale
image = cv2.imread(args['image'])
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# check to see if we should apply thresholding to preprocess the image
if args['preprocess'] == 'thresh':
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

# make a check to see if median blurring should be done to remove noise
# NOTE: I don't think that I'll need this since HQ's questions are
# typically pretty clear
elif args['preprocess'] == 'blur':
    gray = cv2.medianBlur(gray, 3)

# write the grayscale image to disk as a temporary file so we can apply
# OCR to it
filename = "{}.png".format(os.getpid())
cv2.imwrite(filename, gray)

# load the image as a PIL/Pillow image, apply OCR, and then delete the temp
text = pytesseract.image_to_string(Image.open(filename))
text = [x.encode('ascii') for x in text.splitlines()]
os.remove(filename)

# We want to get the question separate from the answers and the other text
# So, we can find the line that has a question mark, move back unit
r = re.compile(".*\?")
newtext = filter(r.match, text)[0]
end_of_q = text.index(newtext)
index = end_of_q
while index > 0 and text[index] != '':
    index -= 1
length_of_q = end_of_q - index + 1
newtext = [x for x in text[index:] if x != ''][:(length_of_q + 2)]
newtext[:-3] = [' '.join(newtext[:-3])]
question = newtext[0]
choices = newtext[1:]
queries = [(question + " \"" + x + "\"") for x in choices]
print queries

# We want to query each of a few search engines in a couple ways
# We want to query Google, DuckDuckGo, Bing
# Each one should be queried at least like question + "choice"
# We might want to query each as question and then search for choice in it
search_results = google.search("This is a sample query", 1)
print search_results[0].number_of_results
