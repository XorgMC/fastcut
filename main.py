import platform
import os
import sys

import vlc

from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *

form_class = uic.loadUiType("./main.ui")[0]

class MyWindow(QMainWindow, form_class, QObject):
    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.setWindowTitle("Python Media Player")

        # Fix window size
        self.setFixedSize(323, 198)

        # Remove resizing mouse cursor
        self.setWindowFlags(QtCore.Qt.MSWindowsFixedSizeDialogHint)

        # Create a basic vlc instance
        self.instance = vlc.Instance()

        # Create an empty vlc media player
        self.mediaplayer = self.instance.media_player_new()

        # Connect signals
        self.btnLoad.clicked.connect(self.load)
        self.btnPlay.clicked.connect(self.play_pause)
        self.btnStop.clicked.connect(self.stop)

        self.media = None
        self.is_paused = False

    def load(self):
        fname = QFileDialog.getOpenFileName(self)
        if not fname:
            return

        # getOpenFileName returns a tuple, so use only the actual file name
        self.media = self.instance.media_new(fname[0])

        # Put the media in the media player
        self.mediaplayer.set_media(self.media)

        # Parse the metadata of the file
        self.media.parse()

        # Set the title of the track as window title
        self.setWindowTitle(self.media.get_meta(0))

        self.play_pause()

    def play_pause(self):
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.btnPlay.setText("Play")
            self.is_paused = True
        else:
            if self.mediaplayer.play() == -1:
                self.load()
                return

            self.mediaplayer.play()
            self.btnPlay.setText("Pause")
            self.is_paused = False

    def stop(self):
        self.mediaplayer.stop()
        self.btnPlay.setText("Play")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    sys.exit(app.exec_())
