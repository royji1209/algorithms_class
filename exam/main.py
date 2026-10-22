import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# Demo implementation for the exam. Cloud Run instances have separate memory;
# for a multi-instance production deployment, store queue state in a shared DB.
queue = []
capacity = 20
front = 0  # index of the first valid element in the circular buffer
size = 0
buffer = [None] * capacity


def reset_queue(new_capacity=20):
    global queue, capacity, front, size, buffer
    capacity = max(1, int(new_capacity))
    front = 0
    size = 0
    buffer = [None] * capacity


def snapshot():
    values = [buffer[(front + i) % capacity] for i in range(size)]
    return {
        "capacity": capacity,
        "count": size,
        "front_index": front,
        "is_empty": size == 0,
        "is_full": size == capacity,
        "front_value": values[0] if values else None,
        "values": values,
        "buffer": buffer,
    }


@app.get("/")
def index():
    return send_from_directory(".", "index.html")


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.route("/api/queue", methods=["GET", "POST"])
def queue_api():
    global front, size, buffer
    if request.method == "GET":
        return jsonify(snapshot())

    data = request.get_json(silent=True) or {}
    action = data.get("action", "")

    try:
        if action == "init":
            reset_queue(data.get("capacity", 20))
            return jsonify({"ok": True, "message": f"큐 크기를 {capacity}로 초기화했습니다.", **snapshot()})

        if action == "push":
            value = data.get("value")
            if value is None:
                return jsonify({"ok": False, "error": "추가할 value가 필요합니다."}), 400
            if size == capacity:
                return jsonify({"ok": False, "error": "큐가 가득 찼습니다(full).", **snapshot()}), 409
            rear = (front + size) % capacity
            buffer[rear] = value
            size += 1
            return jsonify({"ok": True, "message": f"{value}을(를) push했습니다.", **snapshot()})

        if action == "push_many":
            values = data.get("values", [])
            if not isinstance(values, list):
                return jsonify({"ok": False, "error": "values는 배열이어야 합니다."}), 400
            if size + len(values) > capacity:
                return jsonify({"ok": False, "error": "큐 공간이 부족해 전체 데이터를 추가하지 못했습니다.", **snapshot()}), 409
            for value in values:
                rear = (front + size) % capacity
                buffer[rear] = value
                size += 1
            return jsonify({"ok": True, "message": f"{len(values)}개 데이터를 push했습니다.", **snapshot()})

        if action == "pop":
            if size == 0:
                return jsonify({"ok": False, "error": "큐가 비어 있습니다(empty).", **snapshot()}), 409
            value = buffer[front]
            buffer[front] = None
            front = (front + 1) % capacity
            size -= 1
            return jsonify({"ok": True, "popped": value, "message": f"{value}을(를) pop했습니다.", **snapshot()})

        if action == "clear":
            reset_queue(capacity)
            return jsonify({"ok": True, "message": "큐를 비웠습니다.", **snapshot()})

        if action == "find":
            value = data.get("value")
            values = [buffer[(front + i) % capacity] for i in range(size)]
            positions = [i for i, item in enumerate(values) if str(item) == str(value)]
            return jsonify({"ok": True, "value": value, "exists": bool(positions),
                            "logical_indexes": positions, "count": len(positions), **snapshot()})

        if action == "report":
            return jsonify({"ok": True, **snapshot()})

        return jsonify({"ok": False, "error": "지원하지 않는 action입니다."}), 400
    except (TypeError, ValueError) as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
