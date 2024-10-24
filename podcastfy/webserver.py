from flask import Flask, request, jsonify
from celery import Celery
from typing import Optional, List, Dict, Any

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task
def generate_podcast_task(
    urls: Optional[List[str]] = None,
    url_file: Optional[str] = None,
    transcript_file: Optional[str] = None,
    tts_model: Optional[str] = None,
    transcript_only: bool = False,
    config: Optional[Dict[str, Any]] = None,
    conversation_config: Optional[Dict[str, Any]] = None,
    image_paths: Optional[List[str]] = None,
    is_local: bool = False,
) -> Optional[str]:
    return generate_podcast(
        urls, url_file, transcript_file, tts_model, transcript_only,
        config, conversation_config, image_paths, is_local
    )

@app.route('/generate_podcast', methods=['POST'])
def generate_podcast_api():
    try:
        data = request.json
        task = generate_podcast_task.apply_async(kwargs=data)
        return jsonify({"task_id": task.id}), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    task = generate_podcast_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is waiting for execution'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        response = {
            'state': task.state,
            'status': str(task.info)
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


# curl -X POST http://localhost:5000/generate_podcast \
# -H "Content-Type: application/json" \
# -d '{
#   "urls": ["https://example.com"],
#   "tts_model": "elevenlabs",
#   "config": {
#     "main": {
#       "default_tts_model": "elevenlabs"
#     }
#   },
#   "conversation_config": {
#     "word_count": 150,
#     "conversation_style": ["informal", "friendly"],
#     "podcast_name": "My Custom Podcast"
#   },
#   "is_local": true
# }'
