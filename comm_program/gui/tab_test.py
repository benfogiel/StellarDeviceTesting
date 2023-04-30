"""
This module provides a TestTab widget that runs and displays test data.
"""

from typing import TYPE_CHECKING
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
from PyQt5.QtChart import (
    QChart,
    QChartView,
    QLineSeries,
    QValueAxis,
    QAbstractAxis,
    QAbstractSeries,
)
from PyQt5.QtCore import Qt, QObject, QTimer

if TYPE_CHECKING:
    from comm_program.gui.selected_device import SelectedDevice


TEST_RATE = 250  # ms


class TestTab(QWidget):
    """Test Tab widget for connected device."""

    def __init__(self, device: "SelectedDevice") -> None:
        """Initialize the TestTab widget.

        Args:
            device (SelectedDevice): The connected device that is associated with this tab.
        """
        super().__init__()
        self.device = device
        device.run_test_button = QPushButton("Run Test")
        self.run_test_button = device.run_test_button
        self.run_test_button.setEnabled(False)

        self.mv_series = QLineSeries()
        self.ma_series = QLineSeries()

        self.worker = None

        self.mv_chart = None
        self.ma_chart = None
        self.mv_chart_view = None
        self.ma_chart_view = None
        self.save_button = None
        self.build_test_tab()

    def build_test_tab(self) -> None:
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

    def build_plots(self) -> QHBoxLayout:
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

        axis_titles = [("Time (s)", "Millivolts"), ("Time (s)", "Milliamps")]

        for chart, series, titles in zip(
            [self.mv_chart, self.ma_chart],
            [self.mv_series, self.ma_series],
            axis_titles,
        ):
            axis_x, axis_y = QValueAxis(), QValueAxis()
            axis_x.setTitleText(titles[0])
            axis_y.setTitleText(titles[1])
            chart.addAxis(axis_x, Qt.AlignBottom)
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)

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

    def run_test(self) -> None:
        """Run the test."""
        if (
            self.run_test_button.text() == "Run Test"
            and self.test_duration_input.text() != ""
        ):
            # clear series
            self.mv_series.clear()
            self.ma_series.clear()
            self.worker = Worker(self, TEST_RATE)
            success = self.device.start_device_test(
                float(self.test_duration_input.text()), TEST_RATE
            )
            if success:
                self.worker.start()
            else:
                self.worker = None
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
                self.worker = None
                self.run_test_button.setText("Run Test")

    def update_plots(self, time: float, mv: float, ma: float) -> None:
        """Update the plots with new data.

        Args:
            time (float): The time in seconds.
            mv (float): The millivolt value.
            ma (float): The milliamp value.
        """
        self.save_button.setEnabled(True)
        self.mv_series.append(float(time), float(mv))
        self.ma_series.append(float(time), float(ma))
        update_axis_range(
            self.mv_series, self.mv_chart.axes()[0], self.mv_chart.axes()[1]
        )
        update_axis_range(
            self.ma_series, self.ma_chart.axes()[0], self.ma_chart.axes()[1]
        )

        self.ma_chart_view.update()
        self.mv_chart_view.update()

    def save_results(self) -> None:
        """Save the results of the test to a PDF file."""
        file_name = self.pick_file()
        if not file_name:
            return
        file_path = file_name + ".pdf" if not file_name.endswith(".pdf") else file_name
        mv_chart_cp = copy_chart_properties(self.mv_chart)
        ma_chart_cp = copy_chart_properties(self.ma_chart)
        mv_analysis = analyze_data(self.mv_series)
        ma_analysis = analyze_data(self.ma_series)

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
            "<p>This document presents the results of a test device on a Rocket Lab Electron "
            + "rocket. The data is presented in two charts, showcasing the millivolt and milliamp "
            + "outputs of the device. Fasten your seatbelts and prepare for a thrilling "
            + "data-driven journey into the current condition of the Electron Rocket!</p><br>"
        )

        block_format = QTextBlockFormat()
        block_format.setAlignment(Qt.AlignCenter)

        image1 = format_chart(mv_chart_cp).toImage()
        cursor.insertBlock(block_format)
        cursor.insertImage(image1)
        cursor.insertBlock(block_format)
        cursor.insertHtml("<i>Chart 1: Millivolt outputs of the test device</i>")

        cursor.insertHtml(
            "<br><p>As we can see in Chart 1, the millivolt outputs of our test device provide "
            + "valuable insights into the performance of the Electron rocket. We "
            + f"have a maximum millivolt value of {round(mv_analysis['max'],2)} millivolts, "
            + f"minimum of {round(mv_analysis['min'],2)} millivolts and an average of "
            + f"{round(mv_analysis['avg'],2)} millivolts over a total duration of"
            + f" {round(mv_analysis['duration'],2)} seconds.</p>"
        )

        image2 = format_chart(ma_chart_cp).toImage()
        cursor.insertBlock()
        cursor.insertBlock(block_format)
        cursor.insertImage(image2)
        cursor.insertBlock(block_format)
        cursor.insertHtml("<i>Chart 2: Milliamp outputs of the test device</i>")

        cursor.insertHtml(
            "<br><p>As we can see in Chart 2, we have a maximum millivolt value of"
            + f" {round(ma_analysis['max'],2)} millivolts, minimum of "
            + f"{round(ma_analysis['min'],2)} millivolts and an average of "
            + f"{round(ma_analysis['avg'],2)} millivolts over a total duration of"
            + f" {round(ma_analysis['duration'],2)} seconds.</p>"
        )

        # Insert conclusion
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(
            "<br><p>In conclusion, the data from our Rocket Lab Electron test device "
            + "proves that the vehicle is in good condition and is ready to launch!"
        )

        # Save the QTextDocument to a PDF file
        pdf_writer = QPdfWriter(file_path)
        doc.print_(pdf_writer)

    def pick_file(self) -> None:
        """Open a file dialog to pick a file to save to."""
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save file", "", "PDF Files (*.pdf);;All Files (*)", options=options
        )

        return file_name


class Worker(QObject):
    """Worker that listens for test data and updates plots"""

    def __init__(self, test_tab: TestTab, interval: int) -> None:
        """Initialize the worker.

        Args:
            test_tab (TestTab): The TestTab that the worker is running in.
            interval (int): The interval at which to update the plots (units: ms)
        """
        super().__init__()
        self.device = test_tab.device
        self.update_plot_func = test_tab.update_plots
        self.timer = QTimer(self)
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self.execute)
        self.run_test_button = test_tab.run_test_button
        self.test_status = test_tab.test_status
        self.consecutive_timeout_responses = 0

    @property
    def running(self) -> None:
        """Return whether the worker is running or not."""
        return self.timer.isActive()

    def start(self) -> None:
        """Start the worker."""
        self.timer.start()
        self.run_test_button.setText("Stop Test")
        self.test_status.setText("Status: Test Running...")

    def stop(self, force=False) -> None:
        """Stop the worker.

        Args:
            force (bool): Whether to force prematurely the worker to stop or not.
        """
        self.timer.stop()
        if force:
            self.device.stop_device_test()
        self.run_test_button.setText("Run Test")
        self.test_status.setText("Status: No Test Running")

    def execute(self) -> None:
        """Execute the worker.

        Raises:
            ValueError: If the return from get_status is invalid.
        """
        status = self.device.connected_device.get_status()
        if status is None:
            self.consecutive_timeout_responses += 1
            if self.consecutive_timeout_responses > 1:
                self.stop(force=True)
            return
        self.consecutive_timeout_responses = 0
        if status.get("state") == "TESTING":
            self.update_plot_func(*status["msg"])
        elif status.get("state") == "IDLE":
            self.stop()
        else:
            raise ValueError("invalid return from get_status: ", status)


def update_axis_range(
    series: QAbstractSeries, axis_x: QValueAxis, axis_y: QValueAxis
) -> None:
    """Update the range of an axis based on the range of a series

    Args:
        series (QAbstractSeries): The series to use to update the axis range.
        axis_x (QValueAxis): The X axis to update.
        axis_y (QValueAxis): The Y axis to update.
    """
    points = series.pointsVector()
    xs, ys = zip(*[(point.x(), point.y()) for point in points])
    axis_x.setRange(min(xs), max(xs))
    axis_y.setRange(min(ys), max(ys))


def copy_series(series: QAbstractSeries) -> QAbstractSeries:
    """Copy a series.

    Args:
        series (QAbstractSeries): The series to copy.

    Returns:
        QAbstractSeries: A copy of the series.
    """
    if not isinstance(series, QLineSeries):
        raise NotImplementedError("Series type not supported")

    new_series = QLineSeries()
    new_series.replace(series.pointsVector())
    new_series.setName(series.name())
    return new_series


def copy_axis(axis: QAbstractAxis) -> QAbstractAxis:
    """Copy an axis.

    Args:
        axis (QAbstractAxis): The axis to copy.

    Returns:
        QAbstractAxis: A copy of the axis.

    Raises:
        NotImplementedError: If the axis type is not supported.
    """
    if not isinstance(axis, QValueAxis):
        raise NotImplementedError("Axis type not supported")

    new_axis = QValueAxis()
    new_axis.setRange(axis.min(), axis.max())
    new_axis.setLabelFormat(axis.labelFormat())
    new_axis.setTitleText(axis.titleText())
    new_axis.setTickCount(axis.tickCount())
    new_axis.setMinorTickCount(axis.minorTickCount())
    new_axis.setLabelsVisible(axis.labelsVisible())
    new_axis.setGridLineVisible(axis.isGridLineVisible())
    new_axis.setMinorGridLineVisible(axis.isMinorGridLineVisible())
    return new_axis


def copy_chart_properties(chart: QChart) -> QChart:
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

    axis_series_map = {
        axis: [
            series
            for series in chart.series()
            if (
                axis.min() <= series.at(0).x() <= axis.max()
                if axis.orientation() == Qt.Horizontal
                else axis.min() <= series.at(0).y() <= axis.max()
            )
        ]
        for axis in chart.axes()
    }

    for series in chart.series():
        new_series = copy_series(series)
        new_chart.addSeries(new_series)

        for axis, mapped_series in axis_series_map.items():
            if series not in mapped_series:
                continue

            new_axis = copy_axis(axis)
            new_chart.addAxis(new_axis, axis.alignment())
            new_series.attachAxis(new_axis)

    new_chart.setAcceptHoverEvents(chart.acceptHoverEvents())
    return new_chart


def format_chart(chart: QChart) -> QChart:
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


def qline_series_to_list(series: QLineSeries) -> list[tuple[float, float]]:
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


def analyze_data(series: QLineSeries) -> dict[str, float]:
    """Analyze the data from a test.

    Args:
        series (QLineSeries): The series containing the data to analyze.

    Returns:
        dict: A dictionary containing the analysis results.
    """
    points_list = qline_series_to_list(series)
    values = [y for _, y in points_list]
    duration = points_list[-1][0] - points_list[0][0]

    return {
        "max": max(values),
        "min": min(values),
        "avg": sum(values) / len(values),
        "duration": duration,
    }
