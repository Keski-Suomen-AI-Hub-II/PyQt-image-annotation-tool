import csv
import os
import shutil
import sys

import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QIntValidator, QKeySequence
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QCheckBox, QFileDialog, QDesktopWidget, QLineEdit, \
    QRadioButton, QShortcut, QScrollArea, QVBoxLayout, QGroupBox, QFormLayout, QSizePolicy, QAction, QMenu, QMainWindow

from PIL import Image
from pydicom import dcmread

def get_img_paths(dir, extensions=('.png', 'jpg', '.jpeg', 'dcm')):
    '''
    :param dir: folder with files
    :param extensions: tuple with file endings. e.g. ('.png', 'jpg'). Files with these endings will be added to img_paths
    :return: list of all filenames
    '''
    img_paths = []
    for filename in os.listdir(dir):

        if filename.lower().endswith(extensions):
            current_file = os.path.join(dir, filename)
            img_paths.append(current_file)
    return img_paths


def make_folder(directory):
    """
    Make folder if it doesn't already exist
    :param directory: The folder destination path
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


class SetupWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Window variables
        self.width = 800
        self.height = 940

        # State variables
        self.selected_folder = './img' # for saving time
        self.selected_labels = ''
        self.num_labels = 0
        self.label_inputs = []
        self.label_headlines = []
        self.mode = 'csv'  # default option

        # Labels
        self.headline_folder = QLabel('1. Select folder containing images you want to label', self)
        self.headline_num_labels = QLabel('3. Specify labels', self)
        self.labels_file_description = QLabel(
            'a) select file with labels (text file containing one label on each line)', self)
        self.labels_inputs_description = QLabel('b) or specify how many unique labels you want to assign', self)

        # self.headline_num_labels = QLabel('3. How many unique labels do you want to assign?', self)

        self.selected_folder_label = QLabel(self)
        self.selected_folder_label.setText(self.selected_folder)

        self.error_message = QLabel(self)
        # Buttons
        self.browse_button = QtWidgets.QPushButton("Browse", self)
        self.confirm_num_labels = QtWidgets.QPushButton("Ok", self)
        self.next_button = QtWidgets.QPushButton("Next", self)
        self.browse_labels_button = QtWidgets.QPushButton("Select labels", self)

        # Inputs
        self.numLabelsInput = QLineEdit(self)

        # Validation
        self.onlyInt = QIntValidator()

        #layouts
        self.formLayout =QFormLayout()

        #GroupBoxs
        self.groupBox = QGroupBox()

        #Scrolls
        self.scroll = QScrollArea(self)

        # Init
        self.init_ui()

    def init_ui(self):
        # self.selectFolderDialog = QFileDialog.getExistingDirectory(self, 'Select directory')
        self.setWindowTitle('PyQt5 - Annotation tool - Parameters setup')
        self.setGeometry(0, 0, self.width, self.height)
        self.centerOnScreen()

        self.headline_folder.setGeometry(60, 30, 500, 20)
        self.headline_folder.setObjectName("headline")

        self.selected_folder_label.setGeometry(60, 60, 550, 26)
        self.selected_folder_label.setObjectName("selectedFolderLabel")

        self.browse_button.setGeometry(611, 59, 80, 28)
        self.browse_button.clicked.connect(self.pick_new)

        # Input number of labels
        #top_margin_num_labels = 260
        top_margin_num_labels = 115
        self.headline_num_labels.move(60, top_margin_num_labels)
        self.headline_num_labels.setObjectName("headline")

        self.labels_file_description.move(60, top_margin_num_labels + 30)
        # self.browse_labels_button.setGeometry(60, top_margin_num_labels + 60, 80, 28)
        self.browse_labels_button.setGeometry(520, top_margin_num_labels + 25, 89, 28)

        self.browse_labels_button.clicked.connect(self.pick_labels_file)

        # self.labels_inputs_description.move(60, top_margin_num_labels + 100)
        self.labels_inputs_description.move(60, top_margin_num_labels + 60)
        # self.numLabelsInput.setGeometry(60, top_margin_num_labels + 130, 60, 26)
        self.numLabelsInput.setGeometry(75, top_margin_num_labels + 90, 60, 26)

        self.numLabelsInput.setValidator(self.onlyInt)
        self.confirm_num_labels.setGeometry(136, top_margin_num_labels + 89, 80, 28)
        self.confirm_num_labels.clicked.connect(self.generate_label_inputs)

        # Next Button
        #self.next_button.move(360, 630)
        self.next_button.move(360, 490)
        self.next_button.clicked.connect(self.continue_app)
        self.next_button.setObjectName("blueButton")

        # Erro message
        self.error_message.setGeometry(20, 810, self.width - 20, 20)
        self.error_message.setAlignment(Qt.AlignCenter)
        self.error_message.setStyleSheet('color: red; font-weight: bold')

        #self.init_radio_buttons() # for changing modes

        #initiate the ScrollArea
        #self.scroll.setGeometry(60, 400, 300, 200)
        self.scroll.setGeometry(60, 260, 300, 200)
        # apply custom styles
        try:
            styles_path = "./styles.qss"
            with open(styles_path, "r") as fh:
                self.setStyleSheet(fh.read())
        except:
            print("Can't load custom stylesheet.")

        # preloads input fields with predefined labels
        labels = ['Spiking', 'No spiking', 'Unsure']
        print(labels)
        self.numLabelsInput.setText(str(len(labels)))
        self.generate_label_inputs()

        # fill the input fileds with loaded labels
        for input, label in zip(self.label_inputs, labels):
            input.setText(label)

    def init_radio_buttons(self):
        """
        Creates section with mode selection
        """
        
        top_margin = 115
        radio_label = QLabel('2. Select mode', self)
        radio_label.setObjectName("headline")
        radio_label.move(60, top_margin)
        
        radiobutton = QRadioButton(
            "csv (Images in selected folder are labeled and then csv file with assigned labels is generated)", self)
        radiobutton.setChecked(True)
        radiobutton.mode = "csv"
        radiobutton.toggled.connect(self.mode_changed)
        radiobutton.move(60, top_margin + 35)

        radiobutton = QRadioButton(
            "copy (Creates folder for each label. Labeled images are copied to these folders. Csv is also generated)",
            self)
        radiobutton.mode = "copy"
        radiobutton.toggled.connect(self.mode_changed)
        radiobutton.move(60, top_margin + 65)
        
    def mode_changed(self):
        """
        Sets new mode (one of: csv, copy, move)
        """
        radioButton = self.sender()
        if radioButton.isChecked():
            self.mode = radioButton.mode

    def pick_new(self):
        """
        shows a dialog to choose folder with images to label
        """
        dialog = QFileDialog()
        folder_path = dialog.getExistingDirectory(None, "Select Folder")

        self.selected_folder_label.setText(folder_path)
        self.selected_folder = folder_path

    def pick_labels_file(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Select labels", "",
                                                  "Text files (*.txt)", options=options)
        if fileName:
            with open(fileName) as f:
                content = f.readlines()

            labels = [line.rstrip('\n') for line in content]

            print(labels)
            self.numLabelsInput.setText(str(len(labels)))
            self.generate_label_inputs()

            # fill the input fileds with loaded labels
            for input, label in zip(self.label_inputs, labels):
                input.setText(label)

    def generate_label_inputs(self):
        """
        Generates input fields for labels. The layout depends on the number of labels.
        """

        # check that number of labels is not empty
        if self.numLabelsInput.text().strip() != '':

            # convert string (number of labels) to integer
            self.num_labels = int(self.numLabelsInput.text())

            # delete previously generated widgets
            for input, headline in zip(self.label_inputs, self.label_headlines):
                input.deleteLater()
                headline.deleteLater()

            # initialize values
            self.label_inputs = []
            self.label_headlines = []  # labels to label input fields
            margin_top = 400

            # show headline for this step
            self.groupBox.setTitle('4. Fill in the labels and click "Next"')
            self.groupBox.setStyleSheet('font-weight: bold')

            # diplsay input fields
            for i in range(self.num_labels):
                # append widgets to lists
                self.label_inputs.append(QtWidgets.QLineEdit(self))
                self.label_headlines.append(QLabel(f'label {i + 1}:', self))
                self.formLayout.addRow(self.label_headlines[i], self.label_inputs[i])

            self.groupBox.setLayout(self.formLayout)
            self.scroll.setWidget(self.groupBox)
            self.scroll.setWidgetResizable(True)
    def centerOnScreen(self):
        """
        Centers the window on the screen.
        """
        resolution = QDesktopWidget().screenGeometry()
        self.move(int((resolution.width() / 2) - (self.width / 2)),
                  int((resolution.height() / 2) - (self.height / 2)) - 40)

    def check_validity(self):
        """
        :return: if all the necessary information is provided for proper run of application. And error message
        """
        if self.selected_folder == '':
            return False, 'Input folder has to be selected (step 1)'

        num_labels_input = self.numLabelsInput.text().strip()
        if num_labels_input == '' or num_labels_input == '0':
            return False, 'Number of labels has to be number greater than 0 (step 3).'

        if len(self.label_inputs) == 0:
            return False, "You didn't provide any labels. Select number of labels and press \"Ok\""

        for label in self.label_inputs:
            if label.text().strip() == '':
                return False, 'All label fields has to be filled (step 4).'

        return True, 'Form ok'

    def continue_app(self):
        """
        If the setup form is valid, the LabelerWindow is opened and all necessary information is passed to it
        """
        form_is_valid, message = self.check_validity()

        if form_is_valid:
            label_values = []
            for label in self.label_inputs:
                label_values.append(label.text().strip())

            self.close()
            # show window in full-screen mode (window is maximized)
            LabelerWindow(label_values, self.selected_folder, self.mode).showMaximized()
        else:
            self.error_message.setText(message)


class LabelerWindow(QMainWindow): #class LabelerWindow(QWidget):

    def __init__(self, labels, input_folder, mode):
        super().__init__()

        # init UI state
        self.title = 'PyQt5 - Annotation tool for assigning image classes'
        self.left = 200
        self.top = 100
        self.width = 1100
        self.height = 770
        # img panal size should be square-like to prevent some problems with different aspect ratios
        self.img_panel_width = 650
        self.img_panel_height = 650

        # state variables
        self.counter = 0
        self.input_folder = input_folder
        self.img_paths = get_img_paths(input_folder)
        self.labels = labels
        self.num_labels = len(self.labels)
        self.num_images = len(self.img_paths)
        self.assigned_labels = {}
        self.mode = mode

        # zoom factor for the image in labeler panel 
        self.scale_factor = 1.0

        # initialize list to save all label buttons
        self.label_buttons = []

        # Initialize Labels
        self.image_box = QLabel(self)
        self.image_box.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_box.setScaledContents(True)


        self.img_scroll_area = QScrollArea(self) # for image resizing
        self.img_scroll_area.setObjectName('image_panel')
        self.img_scroll_area.setWidget(self.image_box)
        self.img_scroll_area.viewport().installEventFilter(self) # CTRL + mouse wheel zoom in/out

        self.img_name_label = QLabel(self)
        self.progress_bar = QLabel(self)
        self.curr_image_headline = QLabel('Current image:', self)
        self.labeled_percentage = QLabel(self)
        #self.csv_note = QLabel('(csv will be also generated automatically after closing the app)', self)
        self.csv_generated_message = QLabel(self)
        self.show_next_checkbox = QCheckBox("Automatically show next image when labeled", self)

        # for zoom in/out  
        self.create_actions()
        self.create_menus()

        # create label folders
        if mode == 'copy' or mode == 'move':
            self.create_label_folders(labels, self.input_folder)

        # init UI
        self.init_ui()

    def init_ui(self):

        self.setWindowTitle(self.title)
        # self.setGeometry(self.left, self.top, self.width, self.height) # initial dimension of the window
        self.setMinimumSize(self.width, self.height)  # minimum size of the window

        # create buttons
        self.init_buttons()

        # create 'show next automatically' checkbox
        self.show_next_checkbox.setChecked(False)
        self.show_next_checkbox.setGeometry(self.img_panel_width + 25, 5, 400, 100)

        # image headline
        self.curr_image_headline.setGeometry(20, 2, 300, 110)
        self.curr_image_headline.setObjectName('headline')

        # image name label
        self.img_name_label.setGeometry(125, 2, self.img_panel_width, 110)

        # progress bar (how many images have I labeled so far)
        self.progress_bar.setGeometry(20, 65, self.img_panel_width, 20)

        self.labeled_percentage.setGeometry(20, 85, self.img_panel_width, 20)

        # csv note
        #self.csv_note.setGeometry(self.img_panel_width + 20, 640, 400, 20)

        # message that csv was generated
        self.csv_generated_message.setGeometry(self.img_panel_width + 30, 660, 800, 20)
        self.csv_generated_message.setStyleSheet('color: #43A047')

        # show image
        self.set_image(self.img_paths[0])

        # container for the image
        self.img_scroll_area.setGeometry(20, 120, self.img_panel_width, self.img_panel_height)
        self.img_scroll_area.setAlignment(Qt.AlignCenter)
        #self.image_box.setGeometry(20, 120, self.img_panel_width, self.img_panel_height)

        # image name
        path = self.img_paths[self.counter]
        filename = os.path.split(path)[-1]
        self.img_name_label.setText(filename)

        # progress bar
        self.progress_bar.setText(f'Image 1 of {self.num_images}')

        # labeled %
        self.update_labeled_progress()

        # draw line to for better UX
        ui_line = QLabel(self)
        ui_line.setGeometry(20, 110, 1012, 1)
        ui_line.setStyleSheet('background-color: black')
        
        # apply custom styles
        try:
            styles_path = "./styles.qss"
            with open(styles_path, "r") as fh:
                self.setStyleSheet(fh.read())
        except:
            print("Can't load custom stylesheet.")

    # update labeled out of total images percentage
    def update_labeled_progress(self):
        self.labeled_percentage.setText(f'Labeled: {round(100 * (len(self.assigned_labels) / self.num_images), 2)}%')


    def init_buttons(self):

        # Add "Prev Image" and "Next Image" buttons
        next_prev_top_margin = 70 #50
        prev_im_btn = QtWidgets.QPushButton("[p]rev", self)
        prev_im_btn.move(self.img_panel_width + 20, next_prev_top_margin)
        prev_im_btn.clicked.connect(self.show_prev_image)

        next_im_btn = QtWidgets.QPushButton("[n]ext", self)
        next_im_btn.move(self.img_panel_width + 140, next_prev_top_margin)
        next_im_btn.clicked.connect(self.show_next_image)

        # Add "Prev Image" and "Next Image" keyboard shortcuts
        prev_im_kbs = QShortcut(QKeySequence("p"), self)
        prev_im_kbs.activated.connect(self.show_prev_image)

        next_im_kbs = QShortcut(QKeySequence("n"), self)
        next_im_kbs.activated.connect(self.show_next_image)

        # Add "generate csv file" button
        next_im_btn = QtWidgets.QPushButton("Generate csv", self)
        next_im_btn.move(self.img_panel_width + 30, 600)
        next_im_btn.clicked.connect(lambda state, filename='assigned_classes': self.generate_csv(filename))
        next_im_btn.setObjectName("blueButton")

        # Create button for each label
        x_shift = 0  # variable that helps to compute x-coordinate of button in UI
        for i, label in enumerate(self.labels):
            self.label_buttons.append(QtWidgets.QPushButton(label, self))
            button = self.label_buttons[i]

            # create click event (set label)
            # https://stackoverflow.com/questions/35819538/using-lambda-expression-to-connect-slots-in-pyqt
            button.clicked.connect(lambda state, x=label: self.set_label(x))

            # create keyboard shortcut event (set label)
            # shortcuts start getting overwritten when number of labels >9
            label_kbs = QShortcut(QKeySequence(f"{i+1 % 10}"), self)
            label_kbs.activated.connect(lambda x=label: self.set_label(x))

            # place button in GUI (create multiple columns if there is more than 10 button)
            y_shift = (30 + 10) * (i % 10)
            if (i != 0 and i % 10 == 0):
                x_shift += 120
                y_shift = 0

            button.move(self.img_panel_width + 25 + x_shift, y_shift + 120)

    # When scroll is used together with CTRL (command on Mac) zoom image instead of scrolling the image
    #https://stackoverflow.com/questions/69056259/how-to-prevent-scrolling-while-ctrl-is-pressed-in-pyqt5
    def eventFilter(self, source, event):
        if event.type() == event.Wheel and event.modifiers() & Qt.ControlModifier:
            x = event.angleDelta().y() / 120
            if x > 0:
                self.wheel_in()
            elif x < 0:
                self.wheel_out()
            return True
        return super().eventFilter(source, event)
    
    def create_actions(self):
        """Zoom in and out actions"""
        self.zoom_in_action = QAction("Zoom &In (25%)", self, shortcut="Ctrl++", enabled=True, triggered=self.zoom_in)
        self.zoom_out_action = QAction("Zoom &Out (25%)", self, shortcut="Ctrl+-", enabled=True, triggered=self.zoom_out)

    def create_menus(self):
        """Create a menu item for zoom actions"""
        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoom_in_action)
        self.viewMenu.addAction(self.zoom_out_action)
        self.menuBar().addMenu(self.viewMenu)

    def scale_dicom(self, path):
        """reads dicom pixels from a file and returns a scaled np array"""
        ds = dcmread(path)
        img = ds.pixel_array.astype(float)
        scaled = (np.maximum(img, 0) / img.max()) * 255.0
        scaled = np.uint8(scaled)
        return scaled

    def set_label(self, label):
        """
        Sets the label for just loaded image
        :param label: selected label
        """

        # get image filename from path (./data/images/img1.jpg → img1.jpg)
        img_path = self.img_paths[self.counter]
        img_name = os.path.split(img_path)[-1]

        # if the img has some label already
        if img_name in self.assigned_labels.keys():

            # label is already there = means tht user want's to remove label
            if label in self.assigned_labels[img_name]:
                self.assigned_labels[img_name].remove(label)

                # remove key from dictionary if no labels are assigned to this image
                if len(self.assigned_labels[img_name]) == 0:
                    self.assigned_labels.pop(img_name, None)

                # remove image from appropriate folder
                if self.mode == 'copy':
                    os.remove(os.path.join(self.input_folder, label, img_name))

                elif self.mode == 'move':
                    # label was in assigned labels, so I want to remove it from label folder,
                    # but this was the last label, so move the image to input folder.
                    # Don't remove it, because it it not save anywehre else
                    if img_name not in self.assigned_labels.keys():
                        shutil.move(os.path.join(self.input_folder, label, img_name), self.input_folder)
                    else:
                        # label was in assigned labels and the image is store in another label folder,
                        # so I want to remove it from current label folder
                        os.remove(os.path.join(self.input_folder, label, img_name))

            # label is not there yet. But the image has some labels already
            else:
                # remove other labels
                for l in self.assigned_labels[img_name]:
                    if l != label:
                        self.assigned_labels[img_name].remove(l)

                # add selected label
                self.assigned_labels[img_name].append(label)

                # path to copy/move images
                copy_to = os.path.join(self.input_folder, label)

                # copy/move the image into appropriate label folder
                if self.mode == 'copy':
                    # the image is stored in input_folder, so i can copy it from there (differs from 'move' option)
                    shutil.copy(img_path, copy_to)

                elif self.mode == 'move':
                    # the image doesn't have to be stored in input_folder anymore.
                    # get the path where the image is stored
                    copy_from = os.path.join(self.input_folder, self.assigned_labels[img_name][0], img_name)
                    shutil.copy(copy_from, copy_to)

        else:
            # Image has no labels yet. Set new label and copy/move

            self.assigned_labels[img_name] = [label]
            # move copy images to appropriate directories
            copy_to = os.path.join(self.input_folder, label)

            if self.mode == 'copy':
                shutil.copy(img_path, copy_to)
            elif self.mode == 'move':
                shutil.move(img_path, copy_to)

        # update labeled % progress
        self.update_labeled_progress()

        # load next image
        if self.show_next_checkbox.isChecked():
            self.show_next_image()
        else:
            self.set_button_color(img_name)

    def show_next_image(self):
        """
        loads and shows next image in dataset
        """
        if self.counter < self.num_images - 1:
            self.counter += 1

            path = self.img_paths[self.counter]
            filename = os.path.split(path)[-1]

            # If we have already assigned label to this image and mode is 'move', change the input path.
            # The reason is that the image was moved from '.../input_folder' to '.../input_folder/label'
            if self.mode == 'move' and filename in self.assigned_labels.keys():
                path = os.path.join(self.input_folder, self.assigned_labels[filename][0], filename)

            # reset the image scaling
            self.scale_factor = 1

            self.set_image(path)
            self.img_name_label.setText(filename)
            self.progress_bar.setText(f'Image {self.counter + 1} of {self.num_images}')
            self.set_button_color(filename)
            self.csv_generated_message.setText('')

        # change button color if this is last image in dataset
        elif self.counter == self.num_images - 1:
            path = self.img_paths[self.counter]
            self.set_button_color(os.path.split(path)[-1])

    def show_prev_image(self):
        """
        loads and shows previous image in dataset
        """
        if self.counter > 0:
            self.counter -= 1

            if self.counter < self.num_images:
                path = self.img_paths[self.counter]
                filename = os.path.split(path)[-1]

                # If we have already assigned label to this image and mode is 'move', change the input path.
                # The reason is that the image was moved from '.../input_folder' to '.../input_folder/label'
                if self.mode == 'move' and filename in self.assigned_labels.keys():
                    path = os.path.join(self.input_folder, self.assigned_labels[filename][0], filename)

                # reset the image scaling
                self.scale_factor = 1

                self.set_image(path)
                self.img_name_label.setText(filename)
                self.progress_bar.setText(f'Image {self.counter + 1} of {self.num_images}')

                self.set_button_color(filename)
                self.csv_generated_message.setText('')

    def set_image(self, path):
        """
        displays the image in GUI
        :param path: relative path to the image that should be show
        """
        
        # image is DICOM convert to pixmap
        if path.lower().endswith('.dcm'):
            # read and scale dicom image
            img = self.scale_dicom(path)
            # convert to PIL image (workaround since converting a numpy array to pixmap is complex)
            img = Image.fromarray(img)
            # convert to pixmap
            # https://stackoverflow.com/questions/34697559/pil-image-to-qpixmap-conversion-issue
            img = img.convert("RGBA")
            data = img.tobytes("raw","RGBA")
            image = QImage(data, img.size[0], img.size[1], QImage.Format_ARGB32)
            pixmap = QPixmap.fromImage(image)

        # image is not DICOM, create pixmap normally
        else:
            pixmap = QPixmap(path)
        
        self.image_box.setPixmap(pixmap)
        self.image_box.adjustSize()

        zoom_out_iter = 0 # for avoiding infinite loops

        # the image is larger than the container (at least 50 px larger) 
        # -> scale down iteratively the image until it fits the container
        while self.img_panel_width + 50 < self.image_box.width() or self.img_panel_height + 50 < self.image_box.height():
            self.zoom_out()
            zoom_out_iter +=1
            if zoom_out_iter >= 20: break # max iteration cap for scaling

    # zoom with key press
    def zoom_in(self):
        self.scale_image(1.25)
    def zoom_out(self):
        self.scale_image(0.8)

    # zoom with mouse wheel
    def wheel_in(self):
        self.scale_image(1.05)
    def wheel_out(self):
        self.scale_image(0.95)

    def scale_image(self, factor):
        """scale the image container size with given factor"""
        self.scale_factor *= factor

        # disable zoom in or out if the scale factor is too large or small
        # otherwise the program might crash
        if self.scale_factor > 3.0:
            self.scale_factor = 3.0
            return
        if self.scale_factor < 0.1:
            self.scale_factor = 0.1
            return
        self.image_box.resize(self.scale_factor * self.image_box.pixmap().size())

        # adjust the scroll bar accordingly as the the image is scaled up or down
        self.adjust_scroll_bar(self.img_scroll_area.horizontalScrollBar(), factor)
        self.adjust_scroll_bar(self.img_scroll_area.verticalScrollBar(), factor)

    def adjust_scroll_bar(self, scroll_bar, factor):
        """Adjust the scroll bars so that when zooming in focus remains at the center of the image"""
        scroll_bar.setValue(int(factor * scroll_bar.value()
                               + ((factor - 1) * scroll_bar.pageStep() / 2)))

    def generate_csv(self, out_filename):
        """
        Generates and saves csv file with assigned labels.
        Assigned label is represented as one-hot vector.
        :param out_filename: name of csv file to be generated
        """
        path_to_save = os.path.join(self.input_folder, 'output')
        make_folder(path_to_save)
        csv_file_path = os.path.join(path_to_save, out_filename) + '.csv'

        with open(csv_file_path, "w", newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')

            # write header
            writer.writerow(['img'] + self.labels)

            # write one-hot labels
            for img_name, labels in self.assigned_labels.items():
                labels_one_hot = self.labels_to_zero_one(labels)
                writer.writerow([img_name] + list(labels_one_hot))

        message = f'csv saved to: {csv_file_path}'
        self.csv_generated_message.setText(message)
        print(message)

    def set_button_color(self, filename):
        """
        changes color of button which corresponds to selected label
        :filename filename of loaded image:
        """

        if filename in self.assigned_labels.keys():
            assigned_labels = self.assigned_labels[filename]
        else:
            assigned_labels = []

        for button in self.label_buttons:
            if button.text() in assigned_labels:
                button.setStyleSheet('border: 1px solid #43A047; background-color: #4CAF50; color: white')
            else:
                button.setStyleSheet('background-color: None')

    def closeEvent(self, event):
        """
        This function is executed when the app is closed.
        It automatically generates csv file in case the user forgot to do that
        """
        print("closing the App..")
        self.generate_csv('assigned_classes_automatically_generated')

    def labels_to_zero_one(self, labels):
        """
        Convert number to one-hot vector
        :param number: number which represents for example class index
        :param num_classes: number of classes in dataset so I know how long the vector should be
        :return:
        """

        # create mapping from label name to its index for better efficiency {label : int}
        label_to_int = dict((c, i) for i, c in enumerate(self.labels))

        # initialize array to save selected labels
        zero_one_arr = np.zeros([self.num_labels], dtype=int)
        for label in labels:
            zero_one_arr[label_to_int[label]] = 1

        return zero_one_arr

    @staticmethod
    def create_label_folders(labels, folder):
        for label in labels:
            make_folder(os.path.join(folder, label))

if __name__ == '__main__':
    # run the application
    try:
        app
    except:
        app = QApplication(sys.argv)
        ex = SetupWindow()
        ex.show()
        sys.exit(app.exec_())

