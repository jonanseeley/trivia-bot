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
        path = event.src_path
        # load the example image and convert it to grayscale
        image = cv2.imread(path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        # write the grayscale image to disk as a temporary file so we can apply
        # OCR to it
        filename = "{}.png".format(os.getpid())
        cv2.imwrite(filename, gray)

        # load the image as a PIL/Pillow image, apply OCR, then delete the temp
        text = pytesseract.image_to_string(Image.open(filename))
        text = [x.encode('ascii', 'ignore') for x in text.splitlines()]
        os.remove(filename)

        # We want to get the question separate from the answers and other text
        # So, we can find the line that has a question mark, move back unit
        r = re.compile(".*\?")
        try:
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
