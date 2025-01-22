import face_recognition
import cv2
import numpy as np
import os
from datetime import date
import xlrd
from xlutils.copy import copy as xl_copy

def take_attendance(subject_name):
    try:
        uploads_folder = os.path.join(os.getcwd(), "uploads")
        if not os.path.exists(uploads_folder):
            raise FileNotFoundError("Uploads folder does not exist.")

        known_face_encodings = []
        known_face_names = []

        for file_name in os.listdir(uploads_folder):
            if file_name.endswith((".png", ".jpg", ".jpeg")):
                file_path = os.path.join(uploads_folder, file_name)
                print(f"Processing file: {file_name}")
                image = face_recognition.load_image_file(file_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    known_face_encodings.append(encodings[0])
                    known_face_names.append(os.path.splitext(file_name)[0])
                    print(f"Face detected in: {file_name}")
                else:
                    print(f"No face found in: {file_name}")

        if not known_face_encodings:
            raise ValueError("No valid face encodings found in the uploads folder.")

        # Excel file handling
        excel_file = 'attendance_excel.xls'
        if not os.path.exists(excel_file):
            from xlwt import Workbook
            wb_new = Workbook()
            wb_new.add_sheet('Sheet1')
            wb_new.save(excel_file)

        rb = xlrd.open_workbook(excel_file, formatting_info=True)
        wb = xl_copy(rb)

        if subject_name in rb.sheet_names():
            sheet_index = rb.sheet_names().index(subject_name)
            sheet = wb.get_sheet(sheet_index)
        else:
            sheet = wb.add_sheet(subject_name)
            sheet.write(0, 0, 'Name')
            sheet.write(0, 1, 'Date')
            sheet.write(0, 2, 'Status')

        # Webcam initialization
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            raise RuntimeError("Webcam not accessible.")

        already_attended = []
        row = 1

        while True:
            ret, frame = video_capture.read()
            if not ret:
                break

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                name = "Unknown"

                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]

                # Add attendance for recognized faces
                if name != "Unknown" and name not in already_attended:
                    sheet.write(row, 0, name)
                    sheet.write(row, 1, str(date.today()))
                    sheet.write(row, 2, "Present")
                    already_attended.append(name)
                    row += 1
                    print(f"Attendance marked for: {name}")

                # Scale up face locations to match the original frame
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a red rectangle around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Add the name label below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            cv2.imshow("Attendance Capture", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()
        wb.save(excel_file)
        print("Attendance saved.")

    except Exception as e:
        print("Error:", e)
