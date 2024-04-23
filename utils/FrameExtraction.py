import cv2
import sys
import os

def extract_frames(video_path, output_folder):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Unable to open video file.")
        return
    
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    success, image = cap.read()
    count = 0

    while success:
        if count % int(frame_rate) == 0:  # Extract 1 frame per second
            cv2.imwrite(os.path.join(output_folder, f"frame_{count}.png"), image)
        success, image = cap.read()
        count += 1

    cap.release()

if __name__ == "__main__":
    video_path = sys.argv[1]
    output_folder = sys.argv[2]
    os.makedirs(output_folder, exist_ok=True)
    extract_frames(video_path, output_folder)
