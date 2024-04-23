from rembg import remove
import os
import sys

def remove_background(input_folder, output_folder):
    files = os.listdir(input_folder)
    num = len(files)
    for filename in files:
        if filename.endswith(".png"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            
            with open(input_path, 'rb') as f:
                input_image = f.read()
                output_image = remove(input_image)
            
            with open(output_path, 'wb') as out:
                out.write(output_image)
        print(f"Processed {filename} of {num}")

if __name__ == "__main__":
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    os.makedirs(output_folder, exist_ok=True)
    remove_background(input_folder, output_folder)
