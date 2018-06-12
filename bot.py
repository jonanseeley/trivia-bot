# imports
from PIL import Image
from google import google
import pytesseract
import cv2
import os
import sys
import re
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class MyHandler(PatternMatchingEventHandler):
    patterns = ["*"]

    def process(self, event):
        # load the example image and convert it to grayscale
        path = event.src_path
        image = cv2.imread(path)
        resized = cv2.resize(image, (0, 0), fx=3.0, fy=3.0)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        blur = cv2.GaussianBlur(thresh, (5, 5), 0)

        # write the grayscale image to disk as a temporary file so we can apply
        # OCR to it
        filename = "{}.png".format(os.getpid())
        cv2.imwrite(filename, blur)

        # load the image as a PIL/Pillow image, apply OCR, then delete the temp
        text = pytesseract.image_to_string(Image.open(filename))
        text = [x.encode('ascii', 'ignore') for x in text.splitlines()]
        os.remove(filename)
        print text

        # We want to get the question separate from the answers and other text
        # So, we can find the line that has a question mark, move back unit
        try:
            # Find the index where the question ends
            r = re.compile(".*\?")
            newtext = filter(r.match, text)[0]
            end_of_q = text.index(newtext)
            index = end_of_q
            # Find the index of the beginning of the question
            while index > 0 and text[index] != '':
                index -= 1
            length_of_q = end_of_q - index + 1
            # Remove any empty strings in the array
            newtext = [x for x in text[index:] if x != '']
            print newtext
            newtext[:length_of_q] = [' '.join(newtext[:length_of_q])]
            newtext = newtext[:(length_of_q + 2)]
            question = newtext[0]
            choices = newtext[1:]
            queries = [(question + " \"" + x + "\"") for x in choices]
            # We want to query each of a few search engines in a couple ways
            # We want to query Google, DuckDuckGo, Bing
            # Each one should be queried at least like question + "choice"
            query_responses = [google.search(x, 1) for x in queries]
            for x in xrange(3):
                print choices[x]+": "+str(query_responses[x][0].number_of_results)
        except Exception:
            print "Recognition failed!"

    def on_created(self, event):
        self.process(event)


if __name__ == '__main__':
    args = sys.argv[1:]
    observer = Observer()
    observer.schedule(MyHandler(), path=args[0] if args else '.')
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
