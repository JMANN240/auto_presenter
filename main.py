import main_globals
main_globals.init()
import threading
from main_flask import *
from main_flask_public import *
from main_flask_api import *
from main_cv import *

if __name__ == "__main__":
    getFrameThread = threading.Thread(target=getFrame)
    getFrameThread.name = "get frame thread"

    processFrameThread = threading.Thread(target=processFrame)
    processFrameThread.name = "process frame thread"

    serverThread = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 8000})
    serverThread.name = "server thread"

    getFrameThread.start()
    processFrameThread.start()
    serverThread.start()

    getFrameThread.join()
    processFrameThread.join()
    serverThread.join()