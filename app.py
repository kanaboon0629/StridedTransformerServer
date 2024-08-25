from flask import Flask, request, jsonify, send_file
import subprocess
import os
import traceback
import time

app = Flask(__name__)

# 仮想環境のパスとPythonスクリプトのパスを指定
VENV_PATH = 'myvenv'
SCRIPT_PATH = 'develop_stridedtransformer_pose3d.py'

# デフォルト値を設定
DEFAULT_URL = 'https://youtu.be/cZHn_zmvL9I?si=Sx0p-KhTJqnI4Ro9'
DEFAULT_START = 13
DEFAULT_END = 14
JSON_OUTPUT_PATH = 'output.json'

@app.route('/run-script', methods=['POST'])
def run_script():
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
        command = f'{os.path.join(VENV_PATH, "bin", "python3")} {SCRIPT_PATH} "{url}" {start} {end}'
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
    app.run(host='0.0.0.0', port=5000, debug=True)
