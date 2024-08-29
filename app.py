from flask import Flask, request, jsonify, send_file, Response
import subprocess
import os
import time
import traceback
import threading

app = Flask(__name__)

# 定数
VENV_PATH = 'myvenv'
SCRIPT_FROM_VIDEOFILE = '3d-human-pose-estimation/demo/vis.py'
JSON_OUTPUT_PATH = 'output.json'
VIDEO_OUTPUT_PATH = '3d-human-pose-estimation/demo/video/input_clip.mp4'
VIDEO_NAME = 'input_clip.mp4'
OUTPUT_LOG_PATH = 'output.txt'

# グローバル変数
stop_event = threading.Event()
previous_line = ""

def run_script():
    command = f'{os.path.join(VENV_PATH, "bin", "python3")} {SCRIPT_FROM_VIDEOFILE} --video {VIDEO_NAME}'
    with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=os.environ.copy()) as process:
        with open(OUTPUT_LOG_PATH, 'w') as log_file:
            for line in process.stdout:
                log_file.write(line)
                log_file.flush()
            for line in process.stderr:
                log_file.write(line)
                log_file.flush()
        process.wait()
    stop_event.set()

def get_last_line(log_file_path):
    with open(log_file_path, 'r') as log_file:
        log_file.seek(0, os.SEEK_END)
        file_size = log_file.tell()
        if file_size == 0:
            return None
        log_file.seek(max(file_size - 1024, 0), os.SEEK_SET)
        lines = log_file.readlines()
        if lines:
            return lines[-1].strip()
        return None

def tail_output_log():
    global previous_line
    while (True):
        last_line = get_last_line(OUTPUT_LOG_PATH)
        if last_line and last_line != previous_line:
            break
        else:
            time.sleep(0.5)
    previous_line = last_line
    yield last_line

@app.route('/log')
def stream():
    app.logger.info(f"tail_output_log:{tail_output_log()}")
    return Response(tail_output_log(), content_type='text/plain')

@app.route('/run-script-from-videofile', methods=['POST'])
def run_script_from_videofile():
    # OUTPUT_LOG_PATHの中身を空にする
    open(OUTPUT_LOG_PATH, 'w').close()
    
    try:
        if 'file' not in request.files:
            app.logger.error("No file part in the request")
            raise ValueError("No file part in the request")

        file = request.files['file']
        if file.filename == '':
            app.logger.error("No selected file")
            raise ValueError("No selected file")

        file.save(VIDEO_OUTPUT_PATH)
        app.logger.info(f"Video file saved to: {VIDEO_OUTPUT_PATH}")

        script_thread = threading.Thread(target=run_script)
        script_thread.start()
        script_thread.join()

        if os.path.exists(JSON_OUTPUT_PATH) and os.path.getsize(JSON_OUTPUT_PATH) > 0:
            return send_file(JSON_OUTPUT_PATH, mimetype='application/json', as_attachment=True)

        return jsonify({'error': 'JSON file not generated or is empty'}), 500

    except Exception as e:
        error_message = traceback.format_exc()
        app.logger.error(f"An error occurred: {error_message}")
        return jsonify({'error': str(e), 'details': error_message}), 500

@app.route('/run-script-from-youtube', methods=['POST'])
def run_script_from_youtube():
    try:
        # リクエストデータを取得
        data = request.json
        app.logger.info(f"Received data: {data}")

        # パラメータを取得し、Noneの場合はデフォルト値を使用
        url = data.get('url')
        start = data.get('start')
        end = data.get('end')

        # パラメータの検証
        if start is None or end is None:
            raise ValueError("Start and end parameters must be provided")

        if not isinstance(start, int) or not isinstance(end, int):
            raise ValueError("Start and end parameters must be integers")

        # コマンドの構築
        command = f'{os.path.join(VENV_PATH, "bin", "python3")} {SCRIPT_FROM_YOUTUBE} "{url}" {start} {end}'
        app.logger.info(f"Running command: {command}")

        # コマンドの実行
        result = subprocess.run(command, shell=True, capture_output=True, text=True, env=os.environ.copy())

        # 実行結果をログに出力
        app.logger.info(f"Command stdout: {result.stdout}")
        app.logger.error(f"Command stderr: {result.stderr}")

        # JSONファイルが存在するまで最大10分待機
        for _ in range(600):
            if os.path.exists(JSON_OUTPUT_PATH):
                # 完了メッセージの確認
                if "Generating demo successful!" in result.stdout:
                    return send_file(JSON_OUTPUT_PATH, mimetype='application/json', as_attachment=True)
            time.sleep(1)
        
        # JSONファイルが存在しない場合のエラーレスポンス
        return jsonify({'error': 'JSON file not found or process did not complete in time'}), 500

    except Exception as e:
        error_message = traceback.format_exc()
        app.logger.error(f"An error occurred: {error_message}")
        return jsonify({'error': str(e), 'details': error_message}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

