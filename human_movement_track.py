# Poniższy program realizuje zadanie wizyjnego przechwytywania ruchu człowieka.
# Podstawowe możliwości aplikacji to:
# -	wyświetlanie trzech okien: kalibracji ustawień, podglądu kalibracji, podglądu rzeczywistego,
# -	zapis do pliku ustawionych parametrów przez operatora,
# -	restart położeń obszarów detekcji,
# -	przechwytywanie ruchu znaczników po prawidłowej kalibracji parametrów,
# -	śledzenie ruchu znaczników,
# -	odczytywanie w czasie rzeczywistym położeń śledzonych znaczników
#   w jednostce pikseli,
# -	zapis do pliku odczytu wartości kąta zgięcia kończyny w funkcji czasu
#   z dokładnością dwóch miejsc po przecinku.


import cv2 as cv
import numpy as np
import time
import math


class FileOfNumbers:    # klasa umożliwia odczytywanie i zapisywanie parametrówdo pliku
    def __init__(self, file_name):
        self.__file_name = file_name

    def get_numbers(self):
        with open(self.__file_name, "r") as reader:
            nums_string = reader.read()

        num_list = self.__convert_string_to_list(nums_string)

        return num_list

    def __convert_string_to_list(self, nums_string):
        nums_list = []

        nums_string_list = nums_string.split()
        for nsl in nums_string_list:
            nums_list.append(int(nsl))

        return nums_list

    def save_numbers(self, nums_list):
        nums_string = ""

        for num in nums_list:
            nums_string = nums_string + str(num) + "\n"

        with open(self.__file_name, "w") as writer:
            writer.write(nums_string)

    def add_measure_to_file(self, nums_list):
        nums_string = ""

        for num in nums_list:
            nums_string = nums_string + ("%.2f" % num) + ", "

        nums_string = nums_string + "\n"

        with open(self.__file_name, 'a') as writer:
            writer.write(nums_string)


class TrackbarsView:    # klasa umożliwia wyświetlanie okna kalibracji ustawień oraz ich modyfikację przez operatora
    def __init__(self, namedWinStr):
        self.__namedWindowString = namedWinStr
        cv.namedWindow(self.__namedWindowString)
        cv.resizeWindow(self.__namedWindowString, 400, 350)
        cv.createTrackbar('l-h', self.__namedWindowString, trackbars_pos[0], 180, self.__nothing)
        cv.createTrackbar('l-s', self.__namedWindowString, trackbars_pos[1], 255, self.__nothing)
        cv.createTrackbar('l-v', self.__namedWindowString, trackbars_pos[2], 255, self.__nothing)
        cv.createTrackbar('U-h', self.__namedWindowString, trackbars_pos[3], 180, self.__nothing)
        cv.createTrackbar('U-s', self.__namedWindowString, trackbars_pos[4], 255, self.__nothing)
        cv.createTrackbar('U-v', self.__namedWindowString, trackbars_pos[5], 255, self.__nothing)
        cv.createTrackbar('restart', self.__namedWindowString, 0, 1, self.__nothing)
        cv.createTrackbar('save', self.__namedWindowString, 0, 1, self.__nothing)

    def __nothing(self, x):
        pass

    def get_val_of_trackbars(self):
        global lower_color, upper_color

        l_h = cv.getTrackbarPos('l-h', self.__namedWindowString)
        l_s = cv.getTrackbarPos('l-s', self.__namedWindowString)
        l_v = cv.getTrackbarPos('l-v', self.__namedWindowString)
        U_h = cv.getTrackbarPos('U-h', self.__namedWindowString)
        U_s = cv.getTrackbarPos('U-s', self.__namedWindowString)
        U_v = cv.getTrackbarPos('U-v', self.__namedWindowString)

        restart_markers = cv.getTrackbarPos('restart', self.__namedWindowString)
        if restart_markers == 1:
            marker_0.set_area((320, 30))
            marker_1.set_area((320, 220))
            marker_2.set_area((320, 380))
            cv.setTrackbarPos('restart', self.__namedWindowString, 0)

        save = cv.getTrackbarPos('save', self.__namedWindowString)
        if save == 1:
            trackbars_pos = [l_h, l_s, l_v, U_h, U_s, U_v]
            file_trackbars.save_numbers(trackbars_pos)
            cv.setTrackbarPos('save', self.__namedWindowString, 0)

        lower_color = np.array([l_h, l_s, l_v])
        upper_color = np.array([U_h, U_s, U_v])


class CameraFrame:  # główna klasa projektu, która umożliwia przechwytywanie obrazu z kamery,
    # obróbkę obrazu, wykrywanie konturów, rysowanie konturów oraz wstawianie tekstów w obrazie
    def __init__(self):
        self.__cap = cv.VideoCapture(0)
        self.__frame = None
        self.__m0_center = (0, 0)
        self.__m1_center = (0, 0)
        self.__m2_center = (0, 0)
        self.__alfa = 0.0

    def read_frame(self):
        _, self.__frame = self.__cap.read()
        self.__modify_frame()

    def __modify_frame(self):
        self.__frame = cv.flip(self.__frame, 1)
        blurred = cv.GaussianBlur(self.__frame, (31, 31), 0)
        hsv = cv.cvtColor(blurred, cv.COLOR_BGR2HSV)
        self.__mask = cv.inRange(hsv, lower_color, upper_color)

    def calculate_and_draw(self):
        contours, _ = cv.findContours(self.__mask, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
        m0_finded = False
        m1_finded = False
        m2_finded = False
        for contour in contours:
            area_contour = cv.contourArea(contour)

            if area_contour > 500:
                M = cv.moments(contour)
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                center = (cx, cy)

                try:
                    cv.circle(self.__frame, center, 30, (0, 0, 255), 2)
                except:
                    print('err circle draw')

                if m0_finded == False:
                    m0_finded = marker_0.check_area(self.__frame, center)
                if m1_finded == False:
                    m1_finded = marker_1.check_area(self.__frame, center)
                if m2_finded == False:
                    m2_finded = marker_2.check_area(self.__frame, center)

                if m0_finded and m1_finded and m2_finded:
                    self.__m0_center = marker_0.get_center_area()
                    self.__m1_center = marker_1.get_center_area()
                    self.__m2_center = marker_2.get_center_area()
                    self.__draw_lines()

    def __draw_lines(self):
        cv.line(self.__frame, self.__m0_center, self.__m1_center, (0, 255, 0), 2)
        cv.line(self.__frame, self.__m1_center, self.__m2_center, (0, 255, 0), 2)
        self.__calculate_angle()

    def __calculate_angle(self):
        x0, y0 = self.__m0_center
        x1, y1 = self.__m1_center
        x2, y2 = self.__m2_center

        a_2 = (math.pow(x0-x1, 2) + math.pow(y0-y1, 2))
        b_2 = (math.pow(x1-x2, 2) + math.pow(y1-y2, 2))
        c_2 = (math.pow(x0-x2, 2) + math.pow(y0-y2, 2))
        a = (math.sqrt(a_2))
        b = (math.sqrt(b_2))

        try:
            x = (a_2+b_2-c_2)/(2*a*b)
            self.__alfa = int(math.acos(x) * 57.2957795)

            measure_time = time.time()
            file_measure.add_measure_to_file([measure_time - start_time, self.__alfa])

            self.__draw_angle()

        except ZeroDivisionError:
            print('float division by zero')

    def __draw_angle(self):
        text = str(self.__alfa) + "st."
        cv.putText(self.__frame, text, self.__m1_center, cv.FONT_HERSHEY_COMPLEX, 1, (0, 255,255), 1)

    def show_modified_views(self):
        cv.imshow('Calibration View', self.__mask)
        cv.imshow('Real View', self.__frame)

    def end_capture(self):
        self.__cap.release()
        cv.destroyAllWindows()


class Marker:   # klasa umożliwia tworzenie obszaru detekcji w postaci zielonego kwadratu oraz śledzenie znacznika
    def __init__(self, index, area_center, area_detection):
        self.__index = index
        self.__area_detection = area_detection
        self.set_area(area_center)

    def check_area(self, frame, center):
        if center[0] in range(self.__point_1[0], self.__point_2[0]):
            if center[1] in range(self.__point_1[1], self.__point_2[1]):
                self.set_area(center)
                self.__draw(frame)
                return True

        self.__draw(frame)
        return False

    def set_area(self, area_center):
        self.__area_center = area_center
        self.__point_1 = (area_center[0] - self.__area_detection, area_center[1] - self.__area_detection)
        self.__point_2 = (area_center[0] + self.__area_detection, area_center[1] + self.__area_detection)

    def get_center_area(self):
        return self.__area_center

    def __draw(self, frame):
        cv.rectangle(frame, self.__point_1, self.__point_2, (0,255,0), 1)
        cv.putText(frame, str(self.__index), self.__point_1, cv.FONT_HERSHEY_COMPLEX, 1, (0,255,255), 1)
        org = (self.__area_center[0]-40, self.__area_center[1]+30)
        cv.putText(frame, str(self.__area_center), org, cv.FONT_HERSHEY_COMPLEX_SMALL, 1, (0,255,255), 1)


# główny kod wykonawczy programu, który tworzy obiekty i wywołuje okereślone metody
file_trackbars = FileOfNumbers("Trackbars_positions.txt")
trackbars_pos = file_trackbars.get_numbers()
if len(trackbars_pos) != 6:
    trackbars_pos = [125, 51, 86, 170, 255, 162]

trackbars = TrackbarsView('Calibration Settings')
camera_frame = CameraFrame()

marker_0 = Marker(0, (320, 30), 50)
marker_1 = Marker(1, (320, 220), 70)
marker_2 = Marker(2, (320, 380), 80)

start_time = time.time()
measure_time = 0.0

file_measure = FileOfNumbers("Angle_time_measure.txt")

while True:
    trackbars.get_val_of_trackbars()

    camera_frame.read_frame()
    camera_frame.calculate_and_draw()
    camera_frame.show_modified_views()

    key = cv.waitKey(1)
    if key == 27:
        break

camera_frame.end_capture()