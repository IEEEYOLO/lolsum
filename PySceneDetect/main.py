from scenedetect import *

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from moviepy.editor import *

import sys


class MyApp(QWidget):

    def __init__(self, parent):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('My First Application')
        self.move(300, 300)
        self.resize(400, 200)

        self.bar = QProgressBar()
        self.split_bar = QProgressBar()
        self.highlight_bar = QProgressBar()
        self.button_start = QPushButton('Start', self)
        self.button_cancel = QPushButton('Make HighLight', self)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.bar)
        self.layout.addWidget(self.button_start)
        self.layout.addWidget(self.button_cancel)
        self.layout.addWidget(self.split_bar)

        self.setLayout(self.layout)

        self.show()


class SceneDetector(QObject):
    updateProgress = pyqtSignal(float)
    updateSplitProgress = pyqtSignal(float)
    updateTrainProgress = pyqtSignal(float)
    finished = pyqtSignal()

    def __init__(self, file_name):
        super().__init__()
        self.filename = file_name
        self.output_directory = file_name + "_Scene"

    def detect(self):
        # Create a video_manager point to video file testvideo.mp4. Note that multiple
        # videos can be appended by simply specifying more file paths in the list
        # passed to the VideoManager constructor. Note that appending multiple videos
        # requires that they all have the same frame size, and optionally, framerate.

        video_manager = VideoManager([self.filename])
        scene_manager = SceneManager()

        scene_manager.progressUpdated.connect(self.updateProgress)

        # Add ContentDetector algorithm (constructor takes detector options like threshold).
        scene_manager.add_detector(ContentDetector(threshold=27.0))
        base_timecode = video_manager.get_base_timecode()

        # Set video_manager duration to read frames from 00:00:00 to 00:00:20.
        video_manager.set_duration()

        # Set downscale factor to improve processing speed (no args means default).
        video_manager.set_downscale_factor()

        # Start video_manager.
        video_manager.start()

        # Perform scene detection on video_manager.
        scene_manager.detect_scenes(frame_source=video_manager)

        # Obtain list of detected scenes.
        scene_list = scene_manager.get_scene_list(base_timecode)
        # Like FrameTimecodes, each scene in the scene_list can be sorted if the
        # list of scenes becomes unsorted.

        print('List of scenes obtained:')
        for i, scene in enumerate(scene_list):
            print('    Scene %2d: Start %s / Frame %d, End %s / Frame %d' % (
                i + 1,
                scene[0].get_timecode(), scene[0].get_frames(),
                scene[1].get_timecode(), scene[1].get_frames(),))

        video_paths = video_manager.get_video_paths()
        video_name = os.path.basename(video_paths[0])

        split_name_format = 'Scene-$SCENE_NUMBER-$VIDEO_NAME'

        if split_name_format is None:
            return None
        # If an output directory is defined and the file path is a relative path, open
        # the file handle in the output directory instead of the working directory.
        if self.output_directory is not None and not os.path.isabs(split_name_format):
            file_path = os.path.join(self.output_directory, split_name_format)
        # Now that file_path is an absolute path, let's make sure all the directories
        # exist for us to start writing files there.
        try:
            os.makedirs(os.path.split(os.path.abspath(file_path))[0])
        except OSError:
            pass

        from scenedetect.video_splitter import Splitter
        splitter = Splitter()
        splitter.progress_split_updated.connect(self.updateSplitProgress)
        splitter.split_video_ffmpeg(video_paths, scene_list, file_path,
                                    video_name)
        list_train = []
        list_dir = os.listdir(self.output_directory)
        for item in list_dir:
            # TODO: TRAIN, 진행 상황 출력

            # ...
        if len(list_train) != 0 :
            self.finished.emit()

        list_clip = []
        for high_light in list_train:
            clip = VideoFileClip(high_light)
            list_clip.append(clip)

        result_clip = CompositeVideoClip(list_clip)

        result_clip.write_videofile("High_Light_" + self.filename)

        self.finished.emit()


class Example(QObject):

    def __init__(self, file_name, parent=None):
        super(self.__class__, self).__init__(parent)

        self.gui = MyApp(parent)
        self.worker = SceneDetector(file_name)  # 백그라운드에서 돌아갈 인스턴스 소환
        self.worker_thread = QThread()  # 따로 돌아갈 thread를 하나 생성
        self.worker.moveToThread(self.worker_thread)  # worker를 만들어둔 쓰레드에 넣어줍니다
        self.worker_thread.start()  # 쓰레드를 실행합니다.

        self._connectSignals()  # 시그널을 연결하기 위한 함수를 호출

        self.gui.show()


    def _connectSignals(self):

        self.gui.button_start.clicked.connect(self.worker.detect)
        self.worker.updateProgress.connect(self.gui.bar.setValue)
        self.worker.updateSplitProgress.connect(self.gui.split_bar.setValue)
        self.gui.button_cancel.clicked.connect(self.forceWorkerReset)

    def forceWorkerReset(self):
        if self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
            self.worker_thread.start()



class Window(QWidget):

    def __init__(self):
        super().__init__()

        self.open_file_button = QPushButton("Video open")
        self.open_file_button.clicked.connect(self.on_open_file)

        layout = QVBoxLayout(self)
        layout.addWidget(self.open_file_button)

        self.setFixedSize(400, 200)
        self.show()

    def on_open_file(self):
        file_info = QFileDialog.getOpenFileName(self,
                                                "Open Video", "/home", "Video Files (*.mp4)")

        file_name = QFileInfo(file_info[0]).path()
        print(file_name)
        if file_name:
            ex = Example(file_info[0], self)


        else:
            QMessageBox.about(self, "Warning", "파일을 선택하지 않았습니다.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    # thread = QThread()
    # detector = SceneDetector("aaa.mp4")
    # detector.updateProgress.connect(window.bar.setValue)
    # detector.updateSplitProgress.connect(window.split_bar.setValue)
    # detector.finished.connect(finish)
    # detector.moveToThread(thread)
    # thread.started.connect(detector.detect)
    # thread.start()
    sys.exit(app.exec_())
