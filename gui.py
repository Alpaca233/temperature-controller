#!/usr/bin/env python3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from datetime import datetime
import sys
import csv
from controller import TCMController as TCMController

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class TemperatureUpdateSignal(QObject):
    update = pyqtSignal(float, float)

class TemperatureGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Temperature Controller')
        self.setGeometry(100, 100, 1200, 800)

        # Initialize controller
        self.controller = TCMController("CRCOb13BN11")

        # Setup data
        self.temps1 = []
        self.temps2 = []
        self.times = []
        self.targets1 = []
        self.targets2 = []

        # Setup intervals and windows
        self.query_interval1 = 2
        self.query_interval2 = 2
        self.window_size1 = 60
        self.window_size2 = 60
        self.last_update1 = 0
        self.last_update2 = 0

        # Create update signal to handle thread safety
        self.update_signal = TemperatureUpdateSignal()
        self.update_signal.update.connect(self.handle_temperature_update)

        # Set the temperature callback to emit signal
        self.controller.temperature_updating_callback = self.temperature_callback

        # Setup UI
        self.init_ui()
        self.temp_input1.setText(f"{self.controller.target_temperature_ch1:.2f}")
        self.temp_input2.setText(f"{self.controller.target_temperature_ch2:.2f}")

        self.controller.actual_temp_updating_thread.start()

    def create_plot_controls(self, channel):
        control_widget = QWidget()
        layout = QHBoxLayout(control_widget)

        # Query interval control
        layout.addWidget(QLabel("Query Interval:"))
        interval_input = QSpinBox()
        interval_input.setMinimum(2)
        interval_input.setValue(2)
        interval_input.setSuffix(" s")
        layout.addWidget(interval_input)

        # Window size control
        layout.addWidget(QLabel("Window Size:"))
        window_input = QSpinBox()
        window_input.setMinimum(10)
        window_input.setMaximum(3600)  # 1 hour maximum
        window_input.setValue(60)
        window_input.setSuffix(" s")
        layout.addWidget(window_input)

        # Connect signals
        if channel == 1:
            interval_input.valueChanged.connect(self.set_interval1)
            window_input.valueChanged.connect(self.set_window1)
            self.interval_input1 = interval_input
            self.window_input1 = window_input
        else:
            interval_input.valueChanged.connect(self.set_interval2)
            window_input.valueChanged.connect(self.set_window2)
            self.interval_input2 = interval_input
            self.window_input2 = window_input

        return control_widget

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Create top section for temperature controls
        temp_controls = QWidget()
        temp_controls_layout = QHBoxLayout(temp_controls)

        # Channel 1 Controls
        ch1_control = QGroupBox("Channel 1 Control")
        ch1_control_layout = QVBoxLayout()

        temp_layout1 = QHBoxLayout()
        self.temp_label1 = QLabel("0.0°C")
        self.temp_input1 = QLineEdit()
        self.set_btn1 = QPushButton("Set")
        self.save_btn1 = QPushButton("Save")
        temp_layout1.addWidget(QLabel("Current:"))
        temp_layout1.addWidget(self.temp_label1)
        temp_layout1.addWidget(QLabel("Target:"))
        temp_layout1.addWidget(self.temp_input1)
        temp_layout1.addWidget(QLabel("°C"))
        temp_layout1.addWidget(self.set_btn1)
        temp_layout1.addWidget(self.save_btn1)

        ch1_control_layout.addLayout(temp_layout1)
        ch1_control.setLayout(ch1_control_layout)

        # Channel 2 Controls
        ch2_control = QGroupBox("Channel 2 Control")
        ch2_control_layout = QVBoxLayout()

        temp_layout2 = QHBoxLayout()
        self.temp_label2 = QLabel("0.0°C")
        self.temp_input2 = QLineEdit()
        self.set_btn2 = QPushButton("Set")
        self.save_btn2 = QPushButton("Save")
        temp_layout2.addWidget(QLabel("Current:"))
        temp_layout2.addWidget(self.temp_label2)
        temp_layout2.addWidget(QLabel("Target:"))
        temp_layout2.addWidget(self.temp_input2)
        temp_layout2.addWidget(QLabel("°C"))
        temp_layout2.addWidget(self.set_btn2)
        temp_layout2.addWidget(self.save_btn2)

        ch2_control_layout.addLayout(temp_layout2)
        ch2_control.setLayout(ch2_control_layout)

        # Add controls to top section
        temp_controls_layout.addWidget(ch1_control)
        temp_controls_layout.addWidget(ch2_control)

        # Add top section to main layout
        main_layout.addWidget(temp_controls)

        # Create plots section
        plots = QWidget()
        plots_layout = QHBoxLayout(plots)

        # Channel 1 Plot
        ch1_plot = QGroupBox("Channel 1 Plot")
        ch1_plot_layout = QVBoxLayout()

        # Add plot controls
        ch1_plot_layout.addWidget(self.create_plot_controls(1))

        self.canvas1 = MplCanvas(self, width=5, height=4, dpi=100)
        self.record_btn1 = QPushButton("Start Recording")

        ch1_plot_layout.addWidget(self.canvas1)
        ch1_plot_layout.addWidget(self.record_btn1)
        ch1_plot.setLayout(ch1_plot_layout)

        # Channel 2 Plot
        ch2_plot = QGroupBox("Channel 2 Plot")
        ch2_plot_layout = QVBoxLayout()

        # Add plot controls
        ch2_plot_layout.addWidget(self.create_plot_controls(2))

        self.canvas2 = MplCanvas(self, width=5, height=4, dpi=100)
        self.record_btn2 = QPushButton("Start Recording")

        ch2_plot_layout.addWidget(self.canvas2)
        ch2_plot_layout.addWidget(self.record_btn2)
        ch2_plot.setLayout(ch2_plot_layout)

        # Add plots to plots section
        plots_layout.addWidget(ch1_plot)
        plots_layout.addWidget(ch2_plot)

        # Add plots section to main layout
        main_layout.addWidget(plots)

        # Connect signals
        self.set_btn1.clicked.connect(lambda: self.set_temp(1))
        self.set_btn2.clicked.connect(lambda: self.set_temp(2))
        self.save_btn1.clicked.connect(lambda: self.save_temp(1))
        self.save_btn2.clicked.connect(lambda: self.save_temp(2))
        self.record_btn1.clicked.connect(lambda: self.toggle_record(1))
        self.record_btn2.clicked.connect(lambda: self.toggle_record(2))

    def set_interval1(self, value):
        self.query_interval1 = value

    def set_interval2(self, value):
        self.query_interval2 = value

    def set_window1(self, value):
        self.window_size1 = value
        self._update_plot(self.canvas1, self.temps1, self.controller.target_temperature_ch1, 1)

    def set_window2(self, value):
        self.window_size2 = value
        self._update_plot(self.canvas2, self.temps2, self.controller.target_temperature_ch2, 2)

    def handle_temperature_update(self, temp1, temp2):
        current_time = datetime.now().timestamp()

        # Update Channel 1
        if current_time - self.last_update1 >= self.query_interval1:
            self.temp_label1.setText(f"{temp1:.1f}°C")
            self.temps1.append(temp1)
            self.targets1.append(self.controller.target_temperature_ch1)
            self.times.append(current_time)

            # Write to CSV if recording
            if hasattr(self, 'writer1') and self.record_btn1.text() == "Stop Recording":
                self.writer1.writerow([datetime.fromtimestamp(current_time), temp1, self.controller.target_temperature_ch1])

            self._update_plot(self.canvas1, self.temps1, self.targets1, 1)
            self.last_update1 = current_time

        # Update Channel 2
        if current_time - self.last_update2 >= self.query_interval2:
            self.temp_label2.setText(f"{temp2:.1f}°C")
            self.temps2.append(temp2)
            self.targets2.append(self.controller.target_temperature_ch2)

            # Write to CSV if recording
            if hasattr(self, 'writer2') and self.record_btn2.text() == "Stop Recording":
                self.writer2.writerow([datetime.fromtimestamp(current_time), temp2, self.controller.target_temperature_ch2])

            self._update_plot(self.canvas2, self.temps2, self.targets2, 2)
            self.last_update2 = current_time

        # Cleanup old data
        while self.times and current_time - self.times[0] > max(self.window_size1, self.window_size2):
            self.times.pop(0)
            if self.temps1: self.temps1.pop(0)
            if self.temps2: self.temps2.pop(0)
            if self.targets1: self.targets1.pop(0)
            if self.targets2: self.targets2.pop(0)

    def _update_plot(self, canvas, temps, targets, channel):
        if not temps or not self.times:
            return

        canvas.axes.clear()

        # Plot the data
        canvas.axes.plot(self.times, temps, 'b-', label='Actual')
        canvas.axes.plot(self.times, targets, 'r--', label='Target')

        # Set y-axis limits with padding
        y_min = min(min(temps), min(targets))
        y_max = max(max(temps), max(targets))
        padding = (y_max - y_min) * 0.1 if y_max != y_min else 1.0
        canvas.axes.set_ylim([y_min - padding, y_max + padding])

        # Set x-axis to show window size
        window_size = self.window_size1 if channel == 1 else self.window_size2
        current_time = self.times[-1]
        canvas.axes.set_xlim([current_time - window_size, current_time])

        # Format time axis
        canvas.axes.set_xlabel('Seconds Ago')
        canvas.axes.set_ylabel('Temperature (°C)')
        canvas.axes.set_title(f'Channel {channel} Temperature')
        canvas.axes.grid(True)
        canvas.axes.legend()

        # Convert timestamps to relative time for display
        canvas.axes.set_xticklabels([f"{x:.0f}" for x in current_time - canvas.axes.get_xticks()])

        canvas.draw()

    def set_temp(self, channel):
        temp_input = self.temp_input1 if channel == 1 else self.temp_input2
        try:
            temp = float(temp_input.text())
            self.controller.set_target_temperature(f'TC{channel}', temp)
        except ValueError:
            print(f"Invalid temperature for channel {channel}")

    def save_temp(self, channel):
        self.controller.save_target_temperature(f'TC{channel}')

    def toggle_record(self, channel):
        btn = self.record_btn1 if channel == 1 else self.record_btn2
        if btn.text() == "Start Recording":
            btn.setText("Stop Recording")
            filename = f"temp_ch{channel}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            if channel == 1:
                self.file1 = open(filename, 'w', newline='')
                self.writer1 = csv.writer(self.file1)
                self.writer1.writerow(['Time', 'Actual Temperature', 'Target Temperature'])
            else:
                self.file2 = open(filename, 'w', newline='')
                self.writer2 = csv.writer(self.file2)
                self.writer2.writerow(['Time', 'Actual Temperature', 'Target Temperature'])
        else:
            btn.setText("Start Recording")
            if channel == 1:
                self.file1.close()
            else:
                self.file2.close()

    def temperature_callback(self, temp1, temp2):
        # This runs in the controller thread, emit signal to handle in GUI thread
        self.update_signal.update.emit(temp1, temp2)

    def closeEvent(self, event):
        # Stop the controller's update thread
        self.controller.terminate_temperature_updating_thread = True
        self.controller.actual_temp_updating_thread.join()
        
        # Close any open files
        if hasattr(self, 'file1') and self.file1:
            self.file1.close()
        if hasattr(self, 'file2') and self.file2:
            self.file2.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TemperatureGUI()
    window.show()
    sys.exit(app.exec_())