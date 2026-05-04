import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
import math


class Camera2(QThread):
    frame_update = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.running = False
        self.thresholdMin = 177
        self.thresholdMax = 255
        self.new_brightness_value = 50
        self.new_contrast_value= 0.5
        self.new_sharpness_value =50
        

    def start(self):
        self.running = True
        super().start()

    def stop(self):
        self.running = False
        
    def startloop(self):
        self.measurements_started = True

    def setThreshold(self,value):
        self.thresholdMin = value

    def getThreshold(self):
        return self.thresholdMin
    
    def setThreshold2(self,value):
        self.thresholdMax = value

    def getThreshold2(self):
        return self.thresholdMax
    
    #Brightness
    def setBrightness(self,valuebright):
        self.new_brightness_value = valuebright
        print(valuebright)
    def getBrightness(self):
        return self.new_brightness_value
    #Contrast
    def setCONTRAST(self,value):
        self.new_contrast_value = value
        print(value)
    def getCONTRAST(self):
        return self.new_contrast_value
    #SHARPNESS
    def setSHARPNESS(self,value):
        self.new_sharpness_value = value
    def getSHARPNESS(self):
        return self.new_sharpness_value
    
    
    def run(self):
        cap = cv2.VideoCapture(1)
        cap.set(3, 2592)
        cap.set(4, 1944)
        cap.set(5,5)
        
        angle_deg = None
        angle = None
        average_angle = None
        
        corner_coordinates = []
        angle_values = []  # Açı değerlerini saklamak için bir liste

        max_measurements = 100
        loop_count = 0
        self.measurements_started = False

        while self.running:
            thresholdMin = self.getThreshold()
            thresholdMax = self.getThreshold2()
            self.new_brightness_value = self.getBrightness()
            self.new_contrast_value = self.getCONTRAST()
            self.new_sharpness_value = self.getSHARPNESS()
            cap.set(cv2.CAP_PROP_CONTRAST, self.new_contrast_value)
            cap.set(cv2.CAP_PROP_BRIGHTNESS, self.new_brightness_value)
            cap.set(cv2.CAP_PROP_SHARPNESS, self.new_sharpness_value)
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)          
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, thresholdMin, thresholdMax, 3)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            square_counter = 0
            squares = []
            
            for i in range(len(contours)):
                approx = cv2.approxPolyDP(contours[i], cv2.arcLength(contours[i], True) * 0.02, True)
                if abs(cv2.contourArea(contours[i])) < 100 or not cv2.isContourConvex(approx):
                    continue

                if len(approx) == 4:
                    square_counter += 1
                    squares.append(approx)  

            if square_counter == 4:
                # Koordinat işlemleri burada yapılabilir
                center_coordinate_list = []
                center_x_list = []
                center_y_list = []
                XminYmax = []

                for square in squares:
                    M = cv2.moments(square)
                    if M["m00"] != 0:
                        center_x = int(M['m10'] / M['m00'])
                        center_y = int(M['m01'] / M['m00'])
                        center_coordinate_list.append((center_x, center_y))
                        center_x_list.append(center_x)
                        center_y_list.append(center_y)

                sorted_coordinates = sorted(center_coordinate_list, key=lambda coord: coord[1], reverse=True)
                if len(sorted_coordinates) >= 4:
                    max_y_coordinates = sorted_coordinates[:2]
                    min_y_coordinates = sorted_coordinates[2:]
                    max_y_coordinates.sort(key=lambda coord: coord[0])
                    min_y_coordinates.sort(key=lambda coord: coord[0])
                    xmin = max_y_coordinates[0]
                    xmax = max_y_coordinates[1]
                    xminn = min_y_coordinates[0]
                    xmaxx = min_y_coordinates[1]

                    start_point = (xmin[0], xmin[1])
                    end_point = (xmax[0], xmax[1])

                    cv2.putText(frame, "XminYmax", xmin, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.putText(frame, "XmaxYmax", xmax, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.putText(frame, "XminYmin", xminn, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.putText(frame, "XmaxYmin", xmaxx, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.circle(frame, (xmin[0], xmin[1]), 5, (0, 0, 255), -1)
                    cv2.circle(frame, (xmax[0], xmax[1]), 5, (0, 0, 255), -1)
                    cv2.circle(frame, (xminn[0], xminn[1]), 5, (0, 0, 255), -1)
                    cv2.circle(frame, (xmaxx[0], xmaxx[1]), 5, (0, 0, 255), -1)
                    cv2.line(frame, start_point, end_point, (0, 255, 0), 1)
                    rect = cv2.minAreaRect(squares[0])
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)


                    # İki noktanın koordinatları
                    start_point = (xmin[0], xmin[1])
                    end_point = (xmax[0], xmax[1])

                    # İki nokta arasındaki vektörü hesapla
                    vector = (end_point[0] - start_point[0], end_point[1] - start_point[1])

                    # X ekseni ile vektör arasındaki açıyı hesapla
                    angle_rad = math.atan2(vector[1], vector[0])
                    angle_deg = math.degrees(angle_rad)

                    # Sonucu yazdır
                    #print("Açı (derece):", angle_deg)
                    #cv2.drawContours(frame, [box], 0, (0, 255, 255), 1)

            #Artı Sembolü Tespiti
            # Her kontür için işlem yap
            corner_coordinates = []
            if not self.measurements_started:
                # Ölçümlerin başlaması için "x" tuşuna basılmasını bekleyin

                # key = cv2.waitKey(1)
                # if key == ord('x'):
                    self.measurements_started = True

            if self.measurements_started:
                # Görüntüyü gri tonlamaya çevir
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Kenarları belirlemek için Canny kenar dedektörü uygula
                edges = cv2.Canny(gray, thresholdMin, thresholdMax)

                # Konturları bul
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                min_x = float('inf')
                max_x = -float('inf')
                min_x_coords = None
                max_x_coords = None

                

                # Her kontür için işlem yap
                for contour in contours:
                    # Kontürün alanını hesapla
                    area = cv2.contourArea(contour)

                    # Eğer kontürün alanı belirli bir değerin üstünde ise, + sembolü olarak kabul et
                    if area > 1500 and len(contour) >= 8:  # Örneğin, 12 kenar noktası içeren bir kontur
                        # Konturu çiz
                        cv2.drawContours(frame, [contour], -1, (0, 255, 0), 3)

                        # Maskeleme işlemi
                        mask = np.zeros_like(gray)
                        cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)

                        # Shi-Tomasi köşe dedektörü uygula
                        corners = cv2.goodFeaturesToTrack(gray * mask, maxCorners=12, qualityLevel=0.01, minDistance=10)

                        # Köşelerin belirginleştirilmesi
                        corners = np.int0(corners)
                        sorted_coordinatesplus = []
                        x_coords = []
                        # Köşeleri işaretle
                        for corner in corners:
                            x, y = corner.ravel()
                            corner_coordinates.append((x, y))  # Koordinatları ve sıra numarasını sakla
                            cv2.circle(frame, (x, y), 2, (0, 0, 255), -1)
                            sorted_coordinatesplus = sorted(corner_coordinates, key=lambda coord: coord[1], reverse=True)


                         # X'in minimum ve maksimum noktalarını bul
                        if len(corner_coordinates) >= 4:
                            sorted_coordinates = sorted(corner_coordinates, key=lambda coord: coord[0]) #Sıraladık
                            min_x_coords = sorted_coordinates[:2] #en baş 2 değeri aldık
                            max_x_coords = sorted_coordinates[-2:] # en son 2 değeri aldık

    

                            min_x_coords = sorted(min_x_coords, key=lambda coord: coord[1], reverse=True)
                            max_x_coords = sorted(max_x_coords, key=lambda coord: coord[1], reverse=True)

                            min_x = max(min_x_coords, key=lambda coord: coord[1], default=None)
                            max_x = max(max_x_coords, key=lambda coord: coord[1])


                # # X'in minimum ve maksimum noktalarını kırmızı ile işaretle
                if min_x_coords is not None:
                    cv2.circle(frame, (min_x[0], min_x[1]), 5, (0, 0, 255), -1)
                if max_x_coords is not None:
                    cv2.circle(frame, (max_x[0], max_x[1]), 5, (0, 0, 255), -1)

                # İki noktayı birleştir
                if min_x_coords is not None and max_x_coords is not None:
                    cv2.line(frame, min_x, max_x, (0, 0, 255), 2)

                    # İki nokta arasındaki doğrunun x eksenine göre açısını hesapla
                    angle = math.degrees(math.atan2(max_x[1] - min_x[1], max_x[0] - min_x[0]))
                    #print(f"Açı: {angle} derece")

                    angle_values.append(angle)

                loop_count += 1

                if loop_count >= max_measurements:
                    # Ölçümler tamamlandığında görüntü işleme işlemlerini durdur
                    self.measurements_started = False
                    loop_count = 0

                    if angle_values:
                        # Açı değerlerinin aritmetik ortalamasını hesapla
                        average_angle = sum(angle_values) / len(angle_values)
                        #print(f"Toplam {len(angle_values)} ölçüm sonucu için Açı Ortalaması: {average_angle} derece")
                        angle_values = []
                        

                    else:
                        print("Ölçüm yapılmadı.")


                if average_angle and angle_deg is not None:
                    theta = average_angle-angle_deg
                    print(f"Açı Theta ALL: {theta} derece")

                                   

                                   


            width = 1600
            height = 1200
            height,width=gray.shape[:2]
            q_image = QImage(gray.data, width, height,QImage.Format_Grayscale8)

            self.frame_update.emit(q_image)
        

        cap.release()
