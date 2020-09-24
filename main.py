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
        self.sldrProgress.sliderMoved.connect(self.set_progress)
        self.sldrProgress.sliderPressed.connect(self.set_progress)
        self.sldrVolume.valueChanged.connect(self.set_volume)

        self.sldrProgress.setMaximum(1000)
        self.mediaplayer.audio_set_volume(50)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)

        self.media = None
        self.is_paused = False
        self.is_stopped = True

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
        self.is_stopped = False

        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.btnPlay.setText("Play")
            self.is_paused = True
            self.timer.stop()
        else:
            if self.mediaplayer.play() == -1:
                self.load()
                return

            self.mediaplayer.play()
            self.btnPlay.setText("Pause")
            self.timer.start()
            self.is_paused = False

    def stop(self):
        self.is_stopped = True
        self.mediaplayer.stop()
        self.btnPlay.setText("Play")

    def set_volume(self, value):
        self.mediaplayer.audio_set_volume(value)

    def set_progress(self):
        # The vlc MediaPlayer needs a float value between 0 and 1, Qt uses
        # integer variables, so you need a factor; the higher the factor, the
        # more precise are the results (1000 should suffice).
        
        # Set the media position to where the slider was dragged
        self.timer.stop()
        position = self.sldrProgress.value()
        self.mediaplayer.set_position(position / 1000.0)
        self.timer.start()

    def update_ui(self):
        # Set the slider's position to its corresponding media position
        # Note that the setValue function only takes values of type int,
        # so we must first convert the corresponding media position.

        if not self.media:
            return

        if self.is_stopped:
            self.lbStart.setText("00:00")
            self.sldrProgress.setValue(0)
            return

        media_pos = int(self.mediaplayer.get_position() * 1000)
        media_endTime = self.mediaplayer.get_length() // 1000
        media_curTime = self.mediaplayer.get_time() // 1000

        media_endTimeMin = media_endTime // 60
        media_endTimeSec = media_endTime % 60
        self.lbEnd.setText("%d:%d" % (media_endTimeMin, media_endTimeSec))

        media_curTimeMin = media_curTime // 60
        media_curTimeSec = media_curTime % 60
        self.lbStart.setText("%d:%d" % (media_curTimeMin, media_curTimeSec))

        self.sldrProgress.setValue(media_pos)

        # No need to call this function if nothing is played
        if not self.mediaplayer.is_playing():
            self.timer.stop()

            # After the video finished, the play button stills shows "Pause",
            # which is not the desired behavior of a media player.
            # This fixes that "bug".
            if not self.is_paused:
                self.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    sys.exit(app.exec_())
