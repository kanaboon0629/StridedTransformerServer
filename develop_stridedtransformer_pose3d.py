# -*- coding: utf-8 -*-
import cv2
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
from yt_dlp import YoutubeDL
import moviepy.config as mpc

# `ffmpeg` のパスを指定
ffmpeg_path = os.path.join(base_dir, 'myvenv/bin/ffmpeg/ffmpeg-osx-v3.2.4')
mpc.FFMPEG_BINARY = ffmpeg_path
from moviepy.video.fx.resize import resize
from moviepy.editor import VideoFileClip, AudioFileClip, ImageSequenceClip, CompositeAudioClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import math
import subprocess
import sys

# コマンドライン引数を受け取る
if len(sys.argv) < 4:
    sys.exit(1)

video_url = sys.argv[1]
start_sec = int(sys.argv[2])
end_sec = int(sys.argv[3])

# video_url = "https://youtu.be/wYzGtkcttVE?si=IFku7ImYEIAP7ePM"
# start_sec = 3
# end_sec = 4

(start_pt, end_pt) = (start_sec, end_sec)

download_resolution = 360

full_video_path = os.path.join(base_dir, '3d-human-pose-estimation/demo/video/full_video.mp4')
file_name = 'input_clip.mp4'
input_clip_path = os.path.join(base_dir, '3d-human-pose-estimation/demo/video', file_name)

# 利用可能なフォーマットを取得
print('Getting available formats for the video...')
ydl_opts = {'listformats': True}
with YoutubeDL(ydl_opts) as ydl:
    info_dict = ydl.extract_info(video_url, download=False)
    formats = info_dict.get('formats', [])
    
    # heightがNoneまたは0でないフォーマットのみを対象に最高のフォーマットを選択
    best_format = max(
        (fmt for fmt in formats if fmt.get('height') is not None),
        key=lambda x: x.get('height', 0),
        default=None
    )

if best_format:
    ydl_opts = {'format': best_format['format_id'], 'overwrites': True, 'outtmpl': full_video_path}
    with YoutubeDL(ydl_opts) as ydl:
        print('Downloading video from YouTube...')
        ydl.download([video_url])
else:
    sys.exit(1)

# 指定区間切り抜き
print('Extracting subclip...')
with VideoFileClip(full_video_path) as video:
    subclip = video.subclip(start_pt, end_pt)
    subclip.write_videofile(input_clip_path)

# 動画を読み込み、FPSを変更して別名で保存する関数
def m_speed_change(path_in, path_out, scale_factor, color_flag):
    print('Changing speed of the video...')
    movie = cv2.VideoCapture(path_in)

    fps = movie.get(cv2.CAP_PROP_FPS)
    fps_round = math.floor(fps+1)   
    fps_new = int(fps_round * scale_factor) 
    w = int(movie.get(cv2.CAP_PROP_FRAME_WIDTH))   
    h = int(movie.get(cv2.CAP_PROP_FRAME_HEIGHT))  
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')  
    video = cv2.VideoWriter(path_out, fourcc, fps_new, (w, h), color_flag)  

    while True:
        ret, frame = movie.read()
        if not ret:
            break
        video.write(frame)
    
    movie.release()
    return

path_in = input_clip_path         
slow_motion_filename = 'fps_changed_input_video.mp4'
path_out = os.path.join(base_dir, '3d-human-pose-estimation/demo/video', slow_motion_filename)     
scale_factor = 1/6              
color_flag = True               

# 動画の再生速度を変更する関数を実行
m_speed_change(path_in, path_out, scale_factor, color_flag)

# 3D Human Pose Estimation
subprocess.run(["python3", os.path.join(base_dir, '3d-human-pose-estimation/demo/vis.py'), "--video", file_name])