import platform
import os
import sys

import vlc
import ffmpeg

from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *

form_class = uic.loadUiType("./main.ui")[0]
ffmpeg_binary = "/usr/bin/ffmpeg"

class MyWindow(QMainWindow, form_class, QObject):
    start_time = -1
    end_time = -1
    file_list = []
    file_name = ""
    def __init__(self):
        super().__init__()
        
        self.file_list = sys.argv[1:]

        self.setupUi(self)
        self.setWindowTitle("Python Media Player")

        # Remove resizing mouse cursor
        self.setWindowFlags(QtCore.Qt.MSWindowsFixedSizeDialogHint)

        # Create a basic vlc instance
        self.instance = vlc.Instance()

        # Create an empty vlc media player
        self.mediaplayer = self.instance.media_player_new()
        self.mediaplayer.set_xwindow(self.video_frame.winId())

        # Connect signals
        self.btnLoad.clicked.connect(self.load)
        self.btnPlay.clicked.connect(self.play_pause)
        self.btnStop.clicked.connect(self.stop)
        self.btnStartCut.clicked.connect(self.set_start)
        self.btnEndCut.clicked.connect(self.set_end)
        self.btnStartConv.clicked.connect(self.do_convert)
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

        if(len(self.file_list) > 0):
            self.load_file(self.file_list[0])

    def set_start(self):
        self.start_time = self.mediaplayer.get_time()
    
    def set_end(self):
        self.end_time = self.mediaplayer.get_time()

    def format_seconds_to_hhmmss(self, seconds):
        hours = seconds // (60*60)
        seconds %= (60*60)
        minutes = seconds // 60
        seconds %= 60
        return "%02i:%02i:%02i" % (hours, minutes, seconds)
    
    def format_ms_to_hhmmssms(self, ms):
        hours = ms // (60*60*1000)
        ms %= (60*60*1000)
        minutes = ms // (60*1000)
        ms %= (60*1000)
        seconds = ms // 1000
        ms %= 1000
        return "%02i:%02i:%02i.%03i" % (hours, minutes, seconds,ms)

    def do_convert(self):
        self.mediaplayer.play()
        if self.start_time < 0:
            self.start_time = 0
        if self.end_time <= 0:
            self.end_time = self.mediaplayer.get_length()
        self.stop()
        start_ts = self.format_ms_to_hhmmssms(self.start_time)
        dur_sec = (self.end_time - self.start_time)
        duration = self.format_ms_to_hhmmssms(dur_sec)
        print("Start: ", start_ts, ", Dur: ", duration, dur_sec)
        oname = QFileDialog.getSaveFileName(self)
        if not oname:
            return
        ffc = ffmpeg.input(self.file_name,
         init_hw_device="vaapi=foo:/dev/dri/renderD128",
         hwaccel="vaapi",
         hwaccel_output_format="vaapi",
         hwaccel_device="foo").output(oname[0], t=duration, ss=start_ts, filter_hw_device="foo", vf='format=nv12|vaapi,hwupload', qp=24, vcodec='h264_vaapi', acodec='copy').overwrite_output()
        print(ffc.get_args())
        ffc.run()
        if len(self.file_list) > 1:
            self.file_list.pop(0)
            self.load_file(self.file_list[0])

    def load(self):
        fname = QFileDialog.getOpenFileNames(self)
        if not fname:
            return
        if len(fname[0]) < 1:
            return
        self.file_list = fname[0]
        self.load_file(self.file_list[0])
        
    def load_file(self, filename):
        self.file_name = filename

        # getOpenFileName returns a tuple, so use only the actual file name
        self.media = self.instance.media_new(filename)

        # Put the media in the media player
        self.mediaplayer.set_media(self.media)

        # Parse the metadata of the file
        self.media.parse()

        # Set the title of the track as window title
        self.setWindowTitle(self.media.get_meta(0))

        self.play_pause()

        #self.start_time = 0
        #self.end_time = self.mediaplayer.get_length() // 1000

    def play_pause(self):
        self.is_stopped = False

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
            self.timer.start()
            self.is_paused = False

    def stop(self):
        self.is_stopped = True
        self.mediaplayer.stop()
        self.btnPlay.setText("Play")

    def set_volume(self, value):
        self.mediaplayer.audio_set_volume(value)
        self.lbVol.setText("%s%%" % value)

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
        self.lbEnd.setText("%02d:%02d" % (media_endTimeMin, media_endTimeSec))

        media_curTimeMin = media_curTime // 60
        media_curTimeSec = media_curTime % 60
        self.lbStart.setText("%02d:%02d" % (media_curTimeMin, media_curTimeSec))

        self.sldrProgress.setValue(media_pos)

        # No need to call this function if nothing is played
        #if not self.mediaplayer.is_playing():
            # After the video finished, the play button stills shows "Pause",
            # which is not the desired behavior of a media player.
            # This fixes that "bug".
            #if not self.is_paused:
            #    self.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    sys.exit(app.exec_())
