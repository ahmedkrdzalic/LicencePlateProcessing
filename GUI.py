from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QLineEdit, QFileDialog
from PyQt5.QtWidgets import QMessageBox
import sys
import mysql.connector

import cv2
import imutils
import numpy as np
import pytesseract


class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow,self).__init__()
        self.initUI()

    def initUI(self):
        # DB connecting
        self.DBconnect()
        # Main window set
        self.setGeometry(700, 400, 400, 350)
        self.setWindowTitle("Licence Plate Pass")
        self.setStyleSheet("background-color: #ffffc7;")
        # self.setTextColor("color: #233e8b;")

        self.btnENTER = QtWidgets.QPushButton(self)
        self.btnENTER.setText("ENTER")
        self.btnENTER.setStyleSheet("background-color: #a9f1df;")
        self.btnENTER.clicked.connect(self.btnENTER_clicked)
        self.btnENTER.move(150, 100)

        self.btnEXIT = QtWidgets.QPushButton(self)
        self.btnEXIT.setText("EXIT")
        self.btnEXIT.setStyleSheet("background-color: #a9f1df;")
        self.btnEXIT.clicked.connect(self.btnEXIT_clicked)
        self.btnEXIT.move(150, 150)

        self.btnOVERRIDE = QtWidgets.QPushButton(self)
        self.btnOVERRIDE.setText("Override")
        self.btnOVERRIDE.setStyleSheet("background-color: #a9f1df;")
        self.btnOVERRIDE.clicked.connect(self.btnOVERRIDE_clicked)
        self.btnOVERRIDE.move(280, 300)

        self.textbox = QLineEdit(self)
        self.textbox.move(20, 270)
        # self.textbox.resize(280, 40)
        self.textbox.setStyleSheet("background-color: #a9f1df;")
        self.textbox.setPlaceholderText('Registration/Plates')
        self.textbox.setFocus()

        self.btnPAY = QtWidgets.QPushButton(self)
        self.btnPAY.setText("PAY")
        self.btnPAY.setStyleSheet("background-color: #a9f1df;")
        self.btnPAY.clicked.connect(self.btnPAY_clicked)
        self.btnPAY.move(20, 300)

        self.show()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            return fileName


    def scan_plates(self, fileName):
        try:
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

            img = cv2.imread(fileName, cv2.IMREAD_COLOR)
            img = cv2.resize(img, (394, 291))

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.bilateralFilter(gray, 13, 15, 15)

            edged = cv2.Canny(gray, 30, 200)
            contours = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours = imutils.grab_contours(contours)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
            screenCnt = None

            for c in contours:

                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.018 * peri, True)

                if len(approx) == 4:
                    screenCnt = approx
                    break

            if screenCnt is None:
                detected = 0
                print("No contour detected")
            else:
                detected = 1

            if detected == 1:
                cv2.drawContours(img, [screenCnt], -1, (0, 0, 255), 3)

            mask = np.zeros(gray.shape, np.uint8)
            new_image = cv2.drawContours(mask, [screenCnt], 0, 255, -1, )
            new_image = cv2.bitwise_and(img, img, mask=mask)

            (x, y) = np.where(mask == 255)
            (topx, topy) = (np.min(x), np.min(y))
            (bottomx, bottomy) = (np.max(x), np.max(y))
            Cropped = gray[topx:bottomx + 1, topy:bottomy + 1]

            text = pytesseract.image_to_string(Cropped, config='--psm 11')

            text = text.rstrip()
            print("Detected license plate Number is:", text)
            return text

        except:
            print("can not scan!", " - ", sys.exc_info())

    def btnENTER_clicked(self):
        fileName= self.openFileNameDialog()

        plates = ""
        plates = self.scan_plates(fileName)

        if(plates != ""):
            mydb = self.DBconnect()
            mycursor = mydb.cursor()

            sql = """INSERT INTO log (registration) VALUES ('{}');""".format(plates)

            mycursor.execute(sql)
            mydb.commit()

            self.msgOPEN()

    def btnEXIT_clicked(self):
        fileName = self.openFileNameDialog()

        plates = ""
        plates = self.scan_plates(fileName)

        if (plates != ""):
            mydb = self.DBconnect()
            mycursor = mydb.cursor()

            sql = """SELECT * FROM paid_bracket WHERE registration = '{}' ;""".format(plates)
            mycursor.execute(sql)

            mycursor.fetchall()
            row_count = mycursor.rowcount
            print("number of affected rows: {}".format(row_count))
            if (row_count == 0 or row_count < 0):
                self.msgCLOSE()
            else:
                #delete from both tables
                mycursor1 = mydb.cursor()
                sql = """DELETE FROM log WHERE registration = '{}';""".format(plates)
                mycursor1.execute(sql)
                mydb.commit()
                mycursor1 = mydb.cursor()
                sql = """DELETE FROM paid_bracket WHERE registration = '{}';""".format(plates)
                mycursor1.execute(sql)
                mydb.commit()
                self.msgOPEN()

    def btnOVERRIDE_clicked(self):
        self.msgOPEN()

    def btnPAY_clicked(self):
        plates = self.textbox.text()

        mydb = self.DBconnect()
        mycursor1 = mydb.cursor()
        sql = """INSERT INTO paid_bracket (registration) SELECT registration FROM log WHERE registration = '{}';""".format(plates)
        mycursor1.execute(sql)
        mydb.commit()
        print(plates)
        mycursor1 = mydb.cursor()
        sql = """DELETE FROM log WHERE registration = '{}';""".format(plates)
        mycursor1.execute(sql)
        mydb.commit()
        plates = ""


    def msgOPEN(self):
        msg = QMessageBox()
        msg.setWindowTitle("OPEN")
        msg.setText("GATE OPENED")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

    def msgCLOSE(self):
        msg = QMessageBox()
        msg.setWindowTitle("CLOSE")
        msg.setText("GATE CLOSED")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

    def DBconnect(self):
        try:
            return mysql.connector.connect(
                host="localhost",
                user="root",
                passwd="",
                database="lpp"
            )
        except:
            print("Error: No connection to data base")


def window():
    app = QApplication(sys.argv)
    win = MyWindow()
    win.show()
    sys.exit(app.exec_())

window()