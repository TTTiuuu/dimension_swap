"""
维度互换视频特效制作工具 V5 - 带推荐格式提示
Dimension Swap Video Effect Tool

原理：
- 原视频: 分辨率 W×H, 时长 T 帧, 帧率 FPS
- T-X 互换: 输出分辨率 W×T, 时长 H 帧, 帧率 FPS
- T-Y 互换: 输出分辨率 H×T, 时长 W 帧, 帧率 FPS

推荐格式：
- 16:9 (横屏): T-X 建议用 9:16 竖屏视频 → 输出 16:9
- 9:16 (竖屏): T-Y 建议用 16:9 横屏视频 → 输出 9:16
- 4:3: T-X 建议用 3:4 竖屏 → 输出 4:3
- 3:4: T-Y 建议用 4:3 横屏 → 输出 3:4
"""

import sys
import os
import numpy as np
import cv2
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QFileDialog, QProgressBar,
    QTextEdit, QMessageBox, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent


class DimensionSwapWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, input_path, output_dir, mode):
        super().__init__()
        # input_path 可能是 tuple(path, max_frames) 或 str
        if isinstance(input_path, tuple):
            self.input_path, self.max_frames = input_path
        else:
            self.input_path = input_path
            self.max_frames = None
        self.output_dir = output_dir
        self.mode = mode

    def run(self):
        try:
            self.log.emit(f"开始处理视频: {self.input_path}")
            self.log.emit(f"转换模式: {'T-X互换' if self.mode == 'tx' else 'T-Y互换'}")

            cap = cv2.VideoCapture(self.input_path)
            if not cap.isOpened():
                self.error.emit(f"无法打开视频: {self.input_path}")
                return

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            self.log.emit(f"原视频: {width}x{height}, {total_frames}帧, {fps}fps")

            # 读取所有帧
            self.log.emit("正在读取视频帧...")
            frames = []
            read_limit = self.max_frames if self.max_frames else total_frames
            for i in range(read_limit):
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
                if (i + 1) % 100 == 0:
                    self.progress.emit(int((i + 1) / read_limit * 10))

            cap.release()
            T = len(frames)
            self.log.emit(f"已读取 {T} 帧")

            if T < 2:
                self.error.emit("视频帧数太少")
                return

            basename = os.path.splitext(os.path.basename(self.input_path))[0]
            mode_str = "TX" if self.mode == "tx" else "TY"
            output_path = os.path.join(self.output_dir, f"{basename}_{mode_str}_swap.mp4")

            if self.mode == 'tx':
                # T-X 互换
                out_fps = max(fps, 10)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(output_path, fourcc, out_fps, (width, T))

                self.log.emit(f"输出视频: {width}x{T}, {height}帧, {out_fps}fps")
                duration_sec = height / out_fps
                self.log.emit(f"输出时长: 约 {duration_sec:.1f} 秒")

                for y in range(height):
                    new_frame = np.zeros((T, width, 3), dtype=np.uint8)
                    for t in range(T):
                        new_frame[t, :] = frames[t][y, :]
                    out.write(new_frame)

                    if (y + 1) % 10 == 0:
                        self.progress.emit(10 + int((y + 1) / height * 80))

            else:
                # T-Y 互换
                out_fps = max(fps, 10)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(output_path, fourcc, out_fps, (height, T))

                self.log.emit(f"输出视频: {height}x{T}, {width}帧, {out_fps}fps")
                duration_sec = width / out_fps
                self.log.emit(f"输出时长: 约 {duration_sec:.1f} 秒")

                for x in range(width):
                    new_frame = np.zeros((T, height, 3), dtype=np.uint8)
                    for t in range(T):
                        new_frame[t, :] = frames[t][:, x].reshape(1, -1, 3)
                    out.write(new_frame)

                    if (x + 1) % 10 == 0:
                        self.progress.emit(10 + int((x + 1) / width * 80))

            out.release()

            cap2 = cv2.VideoCapture(output_path)
            out_frames = int(cap2.get(cv2.CAP_PROP_FRAME_COUNT))
            out_w = int(cap2.get(cv2.CAP_PROP_FRAME_WIDTH))
            out_h = int(cap2.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap2.release()

            self.log.emit(f"输出视频: {out_w}x{out_h}, {out_frames}帧")
            self.log.emit(f"转换完成！文件已保存至: {output_path}")
            self.finished.emit(output_path)

        except Exception as e:
            import traceback
            self.error.emit(f"错误: {str(e)}\n{traceback.format_exc()}")


class DropLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 150)
        self.setStyleSheet("""
            QLabel {
                border: 3px dashed #666;
                border-radius: 10px;
                background-color: #f0f0f0;
                color: #666;
                font-size: 14px;
            }
            QLabel:hover {
                border-color: #4a9eff;
                background-color: #e8f4ff;
            }
        """)
        self.setText("拖拽视频文件到此处\n或点击下方按钮选择")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QLabel {
                    border: 3px dashed #4a9eff;
                    border-radius: 10px;
                    background-color: #e8f4ff;
                    color: #4a9eff;
                    font-size: 14px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                border: 3px dashed #666;
                border-radius: 10px;
                background-color: #f0f0f0;
                color: #666;
                font-size: 14px;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            video_file = files[0]
            if video_file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')):
                self.window().set_video_path(video_file)
            else:
                QMessageBox.warning(self, "警告", "请选择视频文件！")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.input_video_path = None
        self.output_dir = None
        self.worker = None
        self.input_fps = 30
        self.input_width = 0
        self.input_height = 0

        self.setWindowTitle("维度互换视频特效工具 V5")
        self.setMinimumSize(650, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 标题
        title_label = QLabel("维度互换视频特效制作工具 V5")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)

        # 说明
        info_label = QLabel("将视频的时间轴(T)与空间轴(X或Y)互换，产生高维降维切片效果")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #666; margin-bottom: 5px;")
        main_layout.addWidget(info_label)

        # 拖放区域
        self.drop_label = DropLabel(self)
        main_layout.addWidget(self.drop_label)

        # 选择按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.select_btn = QPushButton("选择视频文件")
        self.select_btn.setMaximumWidth(150)
        self.select_btn.clicked.connect(self.select_video)
        btn_layout.addWidget(self.select_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # 已选文件显示
        self.file_label = QLabel("未选择文件")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setStyleSheet("color: #999;")
        main_layout.addWidget(self.file_label)

        # 推荐格式提示
        format_group = QGroupBox("推荐格式")
        format_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4a9eff;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        format_layout = QVBoxLayout()

        hint1 = QLabel("📺 <b>16:9 横屏输出</b>：用 <b>9:16 竖屏</b> 视频做 T-X 互换<br>"
                      "&nbsp;&nbsp;&nbsp;例：1080×1920, 30fps → 输出 1080×30, 1080帧 ≈ 36秒")
        hint1.setTextFormat(Qt.TextFormat.RichText)
        hint1.setStyleSheet("color: #333; padding: 3px;")
        format_layout.addWidget(hint1)

        hint2 = QLabel("📱 <b>9:16 竖屏输出</b>：用 <b>16:9 横屏</b> 视频做 T-Y 互换<br>"
                      "&nbsp;&nbsp;&nbsp;例：1920×1080, 30fps → 输出 1080×30, 1920帧 ≈ 64秒")
        hint2.setTextFormat(Qt.TextFormat.RichText)
        hint2.setStyleSheet("color: #333; padding: 3px;")
        format_layout.addWidget(hint2)

        hint3 = QLabel("🖥️ <b>4:3 输出</b>：用 <b>3:4 竖屏</b> 视频做 T-X 互换<br>"
                      "&nbsp;&nbsp;&nbsp;例：768×1024, 30fps → 输出 768×30, 1024帧 ≈ 34秒")
        hint3.setTextFormat(Qt.TextFormat.RichText)
        hint3.setStyleSheet("color: #333; padding: 3px;")
        format_layout.addWidget(hint3)

        hint4 = QLabel("📴 <b>3:4 输出</b>：用 <b>4:3 横屏</b> 视频做 T-Y 互换<br>"
                      "&nbsp;&nbsp;&nbsp;例：1024×768, 30fps → 输出 768×30, 1024帧 ≈ 34秒")
        hint4.setTextFormat(Qt.TextFormat.RichText)
        hint4.setStyleSheet("color: #333; padding: 3px;")
        format_layout.addWidget(hint4)

        format_group.setLayout(format_layout)
        main_layout.addWidget(format_group)

        # 转换模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addStretch()
        mode_label = QLabel("转换模式:")
        mode_layout.addWidget(mode_label)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("T-X 互换 (时间↔宽度)", "tx")
        self.mode_combo.addItem("T-Y 互换 (时间↔高度)", "ty")
        self.mode_combo.setMaximumWidth(200)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)

        # 输出目录选择
        output_layout = QHBoxLayout()
        output_layout.addStretch()
        self.output_btn = QPushButton("选择输出目录")
        self.output_btn.setMaximumWidth(130)
        self.output_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.output_btn)
        self.output_label = QLabel("未选择输出目录")
        self.output_label.setMaximumWidth(350)
        self.output_label.setStyleSheet("color: #999;")
        output_layout.addWidget(self.output_label)
        output_layout.addStretch()
        main_layout.addLayout(output_layout)

        # 开始转换按钮
        self.start_btn = QPushButton("开始转换")
        self.start_btn.setMaximumWidth(200)
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                color: white;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3a8eef; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.start_btn.clicked.connect(self.start_conversion)
        self.start_btn.setEnabled(False)
        main_layout.addWidget(self.start_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(20)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 日志区
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #0f0; font-family: monospace;")
        main_layout.addWidget(self.log_text)

        # 默认输出目录
        self.output_dir = os.path.join(os.path.expanduser("~"), "桌面", "dimension_swap_project", "output")
        self.output_label.setText(self.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def set_video_path(self, path):
        self.input_video_path = path
        self.file_label.setText(os.path.basename(path))
        self.file_label.setStyleSheet("color: #4a9eff;")

        # 读取视频信息
        cap = cv2.VideoCapture(path)
        if cap.isOpened():
            self.input_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.input_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.input_fps = cap.get(cv2.CAP_PROP_FPS)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()

            self.file_label.setText(f"{os.path.basename(path)} ({self.input_width}×{self.input_height}, {self.input_fps}fps, {total}帧)")

            # 检查是否需要裁剪
            mode = self.mode_combo.currentData()
            recommended_frames = self.input_height if mode == 'tx' else self.input_width

            if total > recommended_frames:
                reply = QMessageBox.question(
                    self, "视频长度提醒",
                    f"当前视频 {total} 帧，\n"
                    f"推荐格式建议使用 {recommended_frames} 帧的视频。\n\n"
                    f"是否裁剪到推荐长度（取前 {recommended_frames} 帧）？\n"
                    f"选否则使用全部 {total} 帧。",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.input_video_path = (path, recommended_frames)
                    self.log(f"将裁剪到 {recommended_frames} 帧")
                else:
                    self.input_video_path = (path, total)
                    self.log(f"使用全部 {total} 帧")
            else:
                self.input_video_path = (path, total)

        self.start_btn.setEnabled(True)
        self.log(f"已选择视频: {path}")

    def select_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv);;所有文件 (*)"
        )
        if path:
            self.set_video_path(path)

    def select_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_dir)
        if path:
            self.output_dir = path
            self.output_label.setText(path)
            self.log(f"输出目录: {path}")

    def log(self, msg):
        self.log_text.append(msg)

    def start_conversion(self):
        if not self.input_video_path:
            QMessageBox.warning(self, "警告", "请先选择视频文件！")
            return
        if not self.output_dir:
            QMessageBox.warning(self, "警告", "请先选择输出目录！")
            return

        mode = self.mode_combo.currentData()
        self.start_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.log("=" * 40)
        self.log("开始维度互换转换...")
        self.log("=" * 40)

        self.worker = DimensionSwapWorker(self.input_video_path, self.output_dir, mode)
        self.worker.progress.connect(self.on_progress)
        self.worker.log.connect(self.on_log)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_progress(self, value):
        self.progress_bar.setValue(value)

    def on_log(self, msg):
        self.log(msg)

    def on_finished(self, output_path):
        self.progress_bar.setValue(100)
        self.start_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        QMessageBox.information(self, "完成", f"转换完成！\n{output_path}")

    def on_error(self, msg):
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", msg)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
