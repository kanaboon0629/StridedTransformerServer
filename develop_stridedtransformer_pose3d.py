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

"""# テスト動画のセットアップ
47-62

## 動画のトリミング
"""
# video_url = 'https://youtu.be/cZHn_zmvL9I?si=Sx0p-KhTJqnI4Ro9' #@param {type:"string"}

# # #動画の切り抜き範囲(秒)を指定
# # #30秒以上の場合OOM発生の可能性が高いため注意
# start_sec =  13
# end_sec =  14

# コマンドライン引数を受け取る
if len(sys.argv) < 4:
    print("Usage: script.py <video_url> <start_sec> <end_sec>")
    sys.exit(1)

video_url = sys.argv[1]
start_sec = int(sys.argv[2])
end_sec = int(sys.argv[3])

(start_pt, end_pt) = (start_sec, end_sec)

download_resolution = 360

full_video_path = os.path.join(base_dir, '3d-human-pose-estimation/demo/video/full_video.mp4')
file_name = 'input_clip.mp4'
input_clip_path = os.path.join(base_dir, '3d-human-pose-estimation/demo/video', file_name)

# 利用可能なフォーマットを取得
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

# best_formatがNoneでないことを確認してからダウンロード
if best_format:
    ydl_opts = {'format': best_format['format_id'], 'overwrites': True, 'outtmpl': full_video_path}
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
else:
    print("No valid format found")

# 指定区間切り抜き
with VideoFileClip(full_video_path) as video:
    subclip = video.subclip(start_pt, end_pt)
    subclip.write_videofile(input_clip_path)

"""## スローモーション化
https://watlab-blog.com/2019/09/28/movie-speed/
やらなくても良い↓
"""
# 動画を読み込み、FPSを変更して別名で保存する関数
def m_speed_change(path_in, path_out, scale_factor, color_flag):
    # 動画読み込みの設定
    movie = cv2.VideoCapture(path_in)

    # 動画ファイル保存用の設定
    fps = movie.get(cv2.CAP_PROP_FPS)                                  # 元動画のFPSを取得
    fps_round = math.floor(fps+1)   #fps小数点以下の切り上げ
    fps_new = int(fps_round * scale_factor)                            # 動画保存時のFPSはスケールファクターをかける
    print("scale:{},fps:{},fps_round:{},fps_new:{}".format(scale_factor,fps,fps_round,fps_new))
    w = int(movie.get(cv2.CAP_PROP_FRAME_WIDTH))                            # 動画の横幅を取得
    h = int(movie.get(cv2.CAP_PROP_FRAME_HEIGHT))                           # 動画の縦幅を取得
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')                     # 動画保存時のfourcc設定（mp4用）
    video = cv2.VideoWriter(path_out, fourcc, fps_new, (w, h), color_flag)  # 動画の仕様（ファイル名、fourcc, FPS, サイズ）

    # ファイルからフレームを1枚ずつ取得して動画処理後に保存する
    while True:
        ret, frame = movie.read()        # フレームを取得
        video.write(frame)               # 動画を保存する
        # フレームが取得できない場合はループを抜ける
        if not ret:
            break
    # 撮影用オブジェクトとウィンドウの解放
    movie.release()
    return

path_in = input_clip_path         # 元動画のパス
slow_motion_filename = 'fps_changed_input_video.mp4'
path_out = os.path.join(base_dir, '3d-human-pose-estimation/demo/video', slow_motion_filename)     # 保存する動画のパス
scale_factor = 1/6              # FPSにかけるスケールファクター
color_flag = True               # カラー動画はTrue, グレースケール動画はFalse

# 動画の再生速度を変更する関数を実行
m_speed_change(path_in, path_out, scale_factor, color_flag)

"""## 3D Human Pose Estimation

スローモーション動画でやるなら4行目を実行↓
"""
subprocess.run(["python3", os.path.join(base_dir, '3d-human-pose-estimation/demo/vis.py'), "--video", file_name])