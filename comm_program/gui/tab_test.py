"""
This module provides a TestTab widget that runs and displays test data.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QSizePolicy,
    QFileDialog,
)
from PyQt5.QtGui import (
    QPainter,
    QPdfWriter,
    QTextDocument,
    QTextCursor,
    QTextBlockFormat,
    QDoubleValidator,
)
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtCore import Qt, QObject, QTimer


INTERVAL = 500  # ms


class TestTab(QWidget):
    """Test Tab widget for connected device."""

    def __init__(self, device):
        """Initialize the TestTab widget.

        Args:
            device (Device): The connected device that is associated with this tab.
        """
        super().__init__()
        self.device = device
        device.run_test_button = QPushButton("Run Test")
        self.run_test_button = device.run_test_button
        self.run_test_button.setEnabled(False)

        self.mv_series = QLineSeries()
        self.ma_series = QLineSeries()

        self.build_test_tab()

    def build_test_tab(self):
        """Build the TestTab widget."""
        run_test_layout = QVBoxLayout()

        self.test_status = QLabel("Status: No Test Running")
        run_test_layout.addWidget(self.test_status)

        self.test_duration_input = QLineEdit()
        self.test_duration_input.setPlaceholderText("Enter test duration (seconds)")
        # Set the validator to allow only float values
        float_validator = QDoubleValidator()
        self.test_duration_input.setValidator(float_validator)

        run_test_layout.addWidget(self.test_duration_input)

        self.run_test_button.clicked.connect(self.run_test)
        run_test_layout.addWidget(self.run_test_button)

        run_test_widget = QWidget()
        run_test_widget.setMaximumSize(300, 100)
        run_test_widget.setLayout(run_test_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(run_test_widget)
        main_layout.addLayout(self.build_plots())

        self.setLayout(main_layout)

    def build_plots(self):
        """Build the plots for the TestTab widget.

        Returns:
            QHBoxLayout: The layout containing the plots.
        """
        self.mv_chart = QChart()
        self.mv_chart.legend().hide()
        self.ma_chart = QChart()
        self.ma_chart.legend().hide()

        self.mv_chart.addSeries(self.mv_series)
        self.ma_chart.addSeries(self.ma_series)

        # millivolt chart
        self.axis_X_mv = QValueAxis()
        self.axis_Y_mv = QValueAxis()
        self.axis_X_mv.setTitleText("Time (s)")
        self.axis_Y_mv.setTitleText("Millivolts")
        self.mv_chart.addAxis(self.axis_X_mv, Qt.AlignBottom)
        self.mv_chart.addAxis(self.axis_Y_mv, Qt.AlignLeft)
        self.mv_series.attachAxis(self.axis_X_mv)
        self.mv_series.attachAxis(self.axis_Y_mv)

        # milliamp chart
        self.axis_X_ma = QValueAxis()
        self.axis_Y_ma = QValueAxis()
        self.axis_X_ma.setTitleText("Time (s)")
        self.axis_Y_ma.setTitleText("Milliamps")
        self.ma_chart.addAxis(self.axis_X_ma, Qt.AlignBottom)
        self.ma_chart.addAxis(self.axis_Y_ma, Qt.AlignLeft)
        self.ma_series.attachAxis(self.axis_X_ma)
        self.ma_series.attachAxis(self.axis_Y_ma)

        # Set chart titles
        self.mv_chart.setTitle("Millivolt Test Metrics")
        self.ma_chart.setTitle("Milliamp Test Metrics")

        self.mv_chart_view = QChartView(self.mv_chart)
        self.ma_chart_view = QChartView(self.ma_chart)
        self.mv_chart_view.update()
        self.ma_chart_view.update()
        self.mv_chart_view.setRenderHint(QPainter.Antialiasing)
        self.ma_chart_view.setRenderHint(QPainter.Antialiasing)

        # Set the size policy for chart views
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(1)
        self.mv_chart_view.setSizePolicy(size_policy)
        self.ma_chart_view.setSizePolicy(size_policy)

        # Create the Stop/Save Results button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_results)
        self.save_button.setEnabled(False)

        # Create the layout for the first row
        first_row_layout = QHBoxLayout()
        first_row_layout.addWidget(self.mv_chart_view)
        first_row_layout.addWidget(self.ma_chart_view)

        # Create the layout for the second row
        second_row_layout = QHBoxLayout()
        second_row_layout.addWidget(self.save_button)
        second_row_layout.addStretch()

        # add to main layout
        plot_layout = QVBoxLayout()
        plot_layout.addLayout(first_row_layout)
        plot_layout.addLayout(second_row_layout)

        return plot_layout

    def run_test(self):
        """Run the test."""
        if (
            self.run_test_button.text() == "Run Test"
            and self.test_duration_input.text() != ""
        ):
            # clear series
            self.mv_series.clear()
            self.ma_series.clear()
            self.worker = Worker(self, INTERVAL)
            self.device.connected_device.start_test(
                float(self.test_duration_input.text()), INTERVAL
            )
            self.worker.start()
        elif self.run_test_button.text() == "Stop Test":
            reply = QMessageBox.question(
                self,
                "Confirm Stop",
                "Test is currently running, are you sure you'd like to stop it?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                # check status of worker
                if self.worker.running:
                    self.worker.stop(force=True)
                del self.worker
                self.run_test_button.setText("Run Test")

    def update_plots(self, time, mv, ma):
        """Update the plots with new data."""
        self.save_button.setEnabled(True)
        self.mv_series.append(float(time), float(mv))
        self.ma_series.append(float(time), float(ma))
        update_axis_range(self.mv_series, self.axis_X_mv, self.axis_Y_mv)
        update_axis_range(self.ma_series, self.axis_X_ma, self.axis_Y_ma)

        self.ma_chart_view.update()
        self.mv_chart_view.update()

    def save_results(self):
        """Save the results of the test to a PDF file."""
        file_name = self.pick_file()
        if not file_name:
            return
        file_path = file_name + ".pdf" if not file_name.endswith(".pdf") else file_name
        mv_chart_cp = copy_chart_properties(self.mv_chart)
        ma_chart_cp = copy_chart_properties(self.ma_chart)
        mv_analysis = analyze_data(self.mv_series)
        ma_analysis = analyze_data(self.ma_series)
        print(mv_analysis)

        # Create a QTextDocument
        doc = QTextDocument()

        # Create a QTextCursor to insert elements into the QTextDocument
        cursor = QTextCursor(doc)

        # Insert title
        cursor.insertHtml(
            "<h1 style='text-align: center;'>Rocket Lab Electron Test Device Results</h1><br><br>"
        )

        # Insert description
        cursor.insertHtml(
            "<p>This document presents the results of a test device on a Rocket Lab Electron rocket. "
            "The data is presented in two charts, showcasing the millivolt and milliamp outputs of the device. "
            "Fasten your seatbelts and prepare for a thrilling data-driven journey into the stratosphere of rocket science!</p><br>"
        )

        block_format = QTextBlockFormat()
        block_format.setAlignment(Qt.AlignCenter)

        image1 = format_chart(mv_chart_cp).toImage()
        cursor.insertBlock(block_format)
        cursor.insertImage(image1)
        cursor.insertBlock(block_format)
        cursor.insertHtml("<i>Chart 1: Millivolt outputs of the test device</i>")

        cursor.insertHtml(
            "<br><p>As we can see in Chart 1, the millivolt outputs of our test device provide valuable insights "
            "into the electrifying performance of the Electron rocket. We have a maximum millivolt value of"
            f" {round(mv_analysis['max'],2)} millivolts, minimum of {round(mv_analysis['min'],2)} millivolts"
            f" and an average of {round(mv_analysis['avg'],2)} millivolts over a total duration of"
            f" {round(mv_analysis['duration'],2)} seconds.</p>"
        )

        image2 = format_chart(ma_chart_cp).toImage()
        cursor.insertBlock()
        cursor.insertBlock(block_format)
        cursor.insertImage(image2)
        cursor.insertBlock(block_format)
        cursor.insertHtml("<i>Chart 2: Milliamp outputs of the test device</i>")

        cursor.insertHtml(
            "<br><p>As we can see in Chart 2, we have a maximum millivolt value of"
            f" {round(ma_analysis['max'],2)} millivolts, minimum of {round(ma_analysis['min'],2)} millivolts"
            f" and an average of {round(ma_analysis['avg'],2)} millivolts over a total duration of"
            f" {round(ma_analysis['duration'],2)} seconds.</p>"
        )

        # Insert conclusion
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(
            "<br><p>In conclusion, the data from our Rocket Lab Electron test device demonstrates the "
            "awe-inspiring power and performance of this advanced rocket. As we venture further into the cosmos, "
            "we can only imagine what other electrifying discoveries await us.</p>"
        )

        # Save the QTextDocument to a PDF file
        pdf_writer = QPdfWriter(file_path)
        doc.print_(pdf_writer)

    def pick_file(self):
        """Open a file dialog to pick a file to save to."""
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save file", "", "PDF Files (*.pdf);;All Files (*)", options=options
        )

        return file_name


class Worker(QObject):
    """Worker that listens for test data and updates plots"""

    def __init__(self, testTab, interval):
        """Initialize the worker.

        Args:
            testTab (TestTab): The TestTab that the worker is running in.
            interval (int): The interval at which to update the plots (units: ms)
        """
        super(Worker, self).__init__()
        self.device = testTab.device
        self.update_plot_func = testTab.update_plots
        self.timer = QTimer(self, interval=interval, timeout=self.execute)
        self.run_test_button = testTab.run_test_button
        self.test_status = testTab.test_status

    @property
    def running(self):
        """Return whether the worker is running or not."""
        return self.timer.isActive()

    def start(self):
        """Start the worker."""
        self.timer.start()
        self.run_test_button.setText("Stop Test")
        self.test_status.setText("Status: Test Running...")

    def stop(self, force=False):
        """Stop the worker.

        Args:
            force (bool): Whether to force prematurely the worker to stop or not.
        """
        self.timer.stop()
        if force:
            self.device.connected_device.stop_test()
        self.run_test_button.setText("Run Test")
        self.test_status.setText("Status: No Test Running")

    def execute(self):
        """Execute the worker.

        Raises:
            ValueError: If the return from get_status is invalid.
        """
        status = self.device.connected_device.get_status()
        if status is None:
            return
        elif isinstance(status, tuple):
            self.update_plot_func(*status)
        elif isinstance(status, str) and status == "IDLE":
            self.stop()
        else:
            raise ValueError("invalid return from get_status: ", status)


def update_axis_range(series, axisX, axisY):
    """Update the range of an axis based on the range of a series

    Args:
        series (QAbstractSeries): The series to use to update the axis range.
        axisX (QValueAxis): The X axis to update.
        axisY (QValueAxis): The Y axis to update.
    """
    x_min, x_max, y_min, y_max = (
        float("inf"),
        float("-inf"),
        float("inf"),
        float("-inf"),
    )

    for point in series.pointsVector():
        x_min = min(x_min, point.x())
        x_max = max(x_max, point.x())
        y_min = min(y_min, point.y())
        y_max = max(y_max, point.y())

    axisX.setRange(x_min, x_max)
    axisY.setRange(y_min, y_max)


def copy_series(series):
    """Copy a series.

    Args:
        series (QAbstractSeries): The series to copy.

    Returns:
        QAbstractSeries: A copy of the series.
    """
    if isinstance(series, QLineSeries):
        new_series = QLineSeries()
        new_series.replace(series.pointsVector())
    else:
        raise NotImplementedError("Series type not supported")

    new_series.setName(series.name())
    return new_series


def copy_axis(axis):
    """Copy an axis.

    Args:
        axis (QAbstractAxis): The axis to copy.

    Returns:
        QAbstractAxis: A copy of the axis.

    Raises:
        NotImplementedError: If the axis type is not supported.
    """
    if isinstance(axis, QValueAxis):
        new_axis = QValueAxis()
        new_axis.setRange(axis.min(), axis.max())
        new_axis.setLabelFormat(axis.labelFormat())
        new_axis.setTitleText(axis.titleText())
        new_axis.setTickCount(axis.tickCount())
        new_axis.setMinorTickCount(axis.minorTickCount())
        new_axis.setLabelsVisible(axis.labelsVisible())
        new_axis.setGridLineVisible(axis.isGridLineVisible())
        new_axis.setMinorGridLineVisible(axis.isMinorGridLineVisible())
    else:
        raise NotImplementedError("Axis type not supported")

    return new_axis


def copy_chart_properties(chart):
    """Copy the properties of a chart.

    Args:
        chart (QChart): The chart to copy the properties from.

    Returns:
        QChart: A new chart with the same properties as the original.
    """
    new_chart = QChart()
    new_chart.legend().hide()
    new_chart.setTitle(chart.title())
    new_chart.setAnimationOptions(chart.animationOptions())
    new_chart.setTheme(chart.theme())
    new_chart.setMargins(chart.margins())

    axis_series_map = {}

    for series in chart.series():
        new_series = copy_series(series)
        new_chart.addSeries(new_series)

        for axis in chart.axes():
            if axis not in axis_series_map:
                axis_series_map[axis] = []

            if series in axis_series_map[axis]:
                continue

            if axis.orientation() == Qt.Horizontal:
                if axis.min() <= series.at(0).x() <= axis.max():
                    axis_series_map[axis].append(series)
            else:  # axis.orientation() == Qt.Vertical
                if axis.min() <= series.at(0).y() <= axis.max():
                    axis_series_map[axis].append(series)

    for axis in chart.axes():
        new_axis = copy_axis(axis)
        new_chart.addAxis(new_axis, axis.alignment())
        for series in axis_series_map[axis]:
            new_series = new_chart.series()[chart.series().index(series)]
            new_series.attachAxis(new_axis)

    new_chart.setAcceptHoverEvents(chart.acceptHoverEvents())

    return new_chart


def format_chart(chart):
    """Format a chart.

    Args:
        chart (QChart): The chart to format.

    Returns:
        QChart: The formatted chart.
    """
    temp_chart_view1 = QChartView(chart)
    temp_chart_view1.resize(500, 500)
    img = temp_chart_view1.grab()
    img = img.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return img


def qline_series_to_list(series):
    """Convert a QLineSeries to a list of points.
    
    Args:
        series (QLineSeries): The series to convert.
    
    Returns:
        list: A list of points.
    """
    points_list = []
    for i in range(series.count()):
        point = series.at(i)
        points_list.append((point.x(), point.y()))
    return points_list

def analyze_data(series):
    """Analyze the data from a test.

    Args:
        series (QLineSeries): The series containing the data to analyze.

    Returns:
        dict: A dictionary containing the analysis results.
    """
    series_list = qline_series_to_list(series)

    max_val = max(series_list, key=lambda x: x[1])[1]
    min_val = min(series_list, key=lambda x: x[1])[1]
    avg_val = sum([x[1] for x in series_list]) / len(series_list)
    duration = series_list[-1][0] - series_list[0][0]

    return {
        "max": max_val,
        "min": min_val,
        "avg": avg_val,
        "duration": duration,
    }