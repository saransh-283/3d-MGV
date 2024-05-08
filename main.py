import subprocess
import os
import threading
import time
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)

# Update these paths according to your environment
OPENMVG_BIN = "openMVG/bin"
OPENMVS_BIN = "openMVS"
SENSOR_DB = "openMVG/sensor_width_camera_database.txt"
UTILS_DIR = "utils"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_ascii_art():
    os.system('figlet 3D-MGV | lolcat')
    os.system('echo "3D Model Generation from Video" | lolcat')


def spinner(stop_event, step_info, start_time):
    spinner = ['\\', '|', '/', '-']
    spinner_pos = 0
    while not stop_event.is_set():
        current_time = datetime.now()
        elapsed_time = current_time - start_time
        hours, remainder = divmod(int(elapsed_time.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        current_spinner = spinner[spinner_pos % len(spinner)]
        print(f"\r{Fore.YELLOW}{current_spinner} {step_info}\tTime Taken: {time_str}", end='', flush=True)
        spinner_pos += 1
        time.sleep(0.3)

def run_command(command_obj):
    stop_event = threading.Event()
    step_info = f"{Fore.CYAN}Step {command_obj['step']}/{command_obj['total_steps']}: {Fore.WHITE}{command_obj['title']}"
    start_step_time = datetime.now()
    spinner_thread = threading.Thread(target=spinner, args=(stop_event, step_info, start_step_time))
    spinner_thread.start()

    try:
        result = subprocess.run(command_obj['command'], shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        complete_info = f"Step {command_obj['step']}/{command_obj['total_steps']}: {command_obj['title']}"
        stop_event.set()
        elapsed_step = datetime.now() - start_step_time
        elapsed_str = elapsed_step.seconds // 3600, (elapsed_step.seconds // 60) % 60, elapsed_step.seconds % 60
        print(Fore.GREEN + f"\r\u2713 {complete_info}        Time taken: {'%02d:%02d:%02d' % elapsed_str}", flush=True)
        
    except subprocess.CalledProcessError as e:
        stop_event.set()    
        error_info = f"Step {command_obj['step']}/{command_obj['total_steps']}: {command_obj['title']}"
        print(Fore.RED + f"\r\u2717 {error_info}      Error: {e.stderr.decode().strip()}", flush=True)
        exit(1)
    finally:
        if spinner_thread.is_alive():
            spinner_thread.join()

def get_input_video_path():
    while True:
        video_path = input("Enter the path to the input video: ").strip()
        if os.path.exists(video_path):
            return video_path
        else:
            print(f"{Fore.RED}Error: The video path '{video_path}' does not exist. Please try again.")

def process_video(video_path):
    start_time = datetime.now()

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = os.path.join(os.path.dirname(video_path), "output")
    frames_dir = os.path.join(output_dir, "frames")
    transparent_dir = os.path.join(output_dir, "transparent")
    sfm_dir = os.path.join(output_dir, "sfm")
    mvs_dir = os.path.join(output_dir, "mvs")

    for dir in [output_dir, frames_dir, transparent_dir, sfm_dir, mvs_dir]:
        os.makedirs(dir, exist_ok=True)

    # Adjusted commands
    commands = [
        {"title": "Extracting Frames", "command": f"python3 {UTILS_DIR}/FrameExtraction.py {video_path} {frames_dir}"},
        {"title": "Removing Background", "command": f"python3 {UTILS_DIR}/RemoveBackground.py {frames_dir} {transparent_dir}"},
        {"title": "Intrinsics analysis", "command": f"{OPENMVG_BIN}/openMVG_main_SfMInit_ImageListing -i {transparent_dir} -o {sfm_dir}/matches -d {SENSOR_DB} -f 2304"},
        {"title": "Compute features", "command": f"{OPENMVG_BIN}/openMVG_main_ComputeFeatures -i {sfm_dir}/matches/sfm_data.json -o {sfm_dir}/matches -m SIFT -p ULTRA"},
        {"title": "Pair generation", "command": f"{OPENMVG_BIN}/openMVG_main_PairGenerator -i {sfm_dir}/matches/sfm_data.json -o {sfm_dir}/matches/pairs.bin"},
        {"title": "Compute matches", "command": f"{OPENMVG_BIN}/openMVG_main_ComputeMatches -i {sfm_dir}/matches/sfm_data.json -p {sfm_dir}/matches/pairs.bin -o {sfm_dir}/matches/matches.putative.bin -n AUTO"},
        {"title": "Geometric filtering", "command": f"{OPENMVG_BIN}/openMVG_main_GeometricFilter -i {sfm_dir}/matches/sfm_data.json -m {sfm_dir}/matches/matches.putative.bin -o {sfm_dir}/matches/matches.f.bin"},
        {"title": "Structure from Motion", "command": f"{OPENMVG_BIN}/openMVG_main_SfM -i {sfm_dir}/matches/sfm_data.json -m {sfm_dir}/matches -o {sfm_dir} -s INCREMENTAL"},
        {"title": "Export to OpenMVS", "command": f"{OPENMVG_BIN}/openMVG_main_openMVG2openMVS -i {sfm_dir}/sfm_data.bin -o {mvs_dir}/scene.mvs -d {mvs_dir}"},
        {"title": "Densify point cloud", "command": f"{OPENMVS_BIN}/DensifyPointCloud scene.mvs -w {mvs_dir}"},
        {"title": "ReconstructMesh", "command": f"{OPENMVS_BIN}/ReconstructMesh scene_dense.mvs -w {mvs_dir}"},
        {"title": "Texture mesh", "command": f"{OPENMVS_BIN}/TextureMesh scene_dense.mvs -m scene_dense_mesh.ply -w {mvs_dir} --export-type obj -o {base_name}.obj"}
    ]

    total_steps = len(commands)
    for i, cmd in enumerate(commands, start=1):
        cmd['step'] = i
        cmd['total_steps'] = total_steps
        run_command(cmd)

    # Completion message with updated file naming
    print(f"{Fore.CYAN}{'-'*50}\n{Fore.GREEN}All steps have been completed successfully.")
    total_time = datetime.now() - start_time
    total_str = f"{total_time.seconds // 3600:02d}:{(total_time.seconds // 60) % 60:02d}:{total_time.seconds % 60:02d}"
    print(f"{Fore.CYAN}{'-'*50}\n{Fore.GREEN}Total time taken: {total_str}")
    model_path = os.path.join(mvs_dir, f"{base_name}.obj")
    material_path = os.path.join(mvs_dir, f"{base_name}_00_material_map_Kd.jpg")
    print(f"{Fore.CYAN}Model: {Fore.YELLOW}{model_path}\n{Fore.CYAN}Texture: {Fore.YELLOW}{material_path}")

if __name__ == "__main__":
    clear_screen()
    print_ascii_art()
    video_path = get_input_video_path()
    process_video(video_path)