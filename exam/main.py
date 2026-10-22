import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# 큐 상태 변수
queue = []
capacity = 20
front = 0
size = 0
buffer = [None] * capacity


def reset_queue(new_capacity=20):
    global capacity, front, size, buffer
    capacity = max(1, int(new_capacity))
    front = 0
    size = 0
    buffer = [None] * capacity


def snapshot():
    values = [buffer[(front + i) % capacity] for i in range(size)]
    return {
        "capacity": capacity,
        "count": size,
        "current_size": size,
        "front_index": front,
        "front": front,
        "rear": (front + size) % capacity,
        "is_empty": size == 0,
        "is_full": size == capacity,
        "state_text": "FULL (가득 참)" if size == capacity else ("EMPTY (비어 있음)" if size == 0 else "NORMAL (여유 있음)"),
        "status": {
            "is_empty": size == 0,
            "is_full": size == capacity,
            "state_text": "FULL (가득 참)" if size == capacity else ("EMPTY (비어 있음)" if size == 0 else "NORMAL (여유 있음)")
        },
        "front_value": values[0] if values else None,
        "front_data": values[0] if values else None,
        "values": values,
        "front_to_rear": values,
        "raw_buffer": list(buffer),
        "buffer": list(buffer)
    }


@app.get("/")
def index():
    return send_from_directory(".", "index.html")


@app.get("/health")
def health():
    return jsonify({"ok": True, "status": "healthy"})


@app.route("/api/queue", methods=["GET", "POST", "OPTIONS"])
@app.route("/queue", methods=["GET", "POST", "OPTIONS"])
def queue_api():
    global front, size, buffer
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200

    if request.method == "GET":
        return jsonify(snapshot())

    data = request.get_json(silent=True) or {}
    action = data.get("action", "")

    try:
        # 1) 시나리오 일괄 실행 요청 대응 (1~8번 동작)
        if action == "RUN_SCENARIO":
            cap = int(data.get("capacity", 20))
            input_arr = data.get("array", [19, 15, 29, 25, 33, 35, 49, 42, 50, 55, 62, 66, 77, 80])
            target_search = int(data.get("search_val", 42))
            target_exist = int(data.get("exist_val", 88))

            reset_queue(cap)
            steps = []

            # Step 1: 초기화
            steps.append({
                "step": 1,
                "title": f"1) 큐 초기화 (사이즈 = {cap})",
                "action_type": "INIT",
                "highlight_indices": [],
                "result_text": f"크기 {cap}인 고정 길이 큐를 생성하고 초기화했습니다.",
                "snapshot": snapshot()
            })

            # Step 2: 배열 Push
            for val in input_arr:
                if size < capacity:
                    rear = (front + size) % capacity
                    buffer[rear] = int(val)
                    size += 1

            steps.append({
                "step": 2,
                "title": f"2) 배열 데이터 Push ({len(input_arr)}개 원소 삽입)",
                "action_type": "PUSH_ARRAY",
                "highlight_indices": list(range(len(input_arr))),
                "result_text": f"입력 배열 {input_arr}을(를) 차례대로 Push 완료했습니다.",
                "snapshot": snapshot()
            })

            # Step 3: 현재 개수
            steps.append({
                "step": 3,
                "title": "3) 현재의 데이터 개수(길이/크기) 확인",
                "action_type": "SIZE",
                "highlight_indices": [],
                "result_text": f"현재 큐에 저장된 데이터 개수는 총 {size}개입니다. (최대 용량: {capacity})",
                "snapshot": snapshot()
            })

            # Step 4: 상태 검사
            st = snapshot()["status"]
            steps.append({
                "step": 4,
                "title": "4) 현재 상태 검사 (Full / Empty)",
                "action_type": "STATUS",
                "highlight_indices": [],
                "result_text": f"Empty 여부: {st['is_empty']} | Full 여부: {st['is_full']} -> 상태: {st['state_text']}",
                "snapshot": snapshot()
            })

            # Step 5: 전면 데이터 확인
            pk_val = buffer[front] if size > 0 else None
            steps.append({
                "step": 5,
                "title": "5) 전면(Front) 데이터 확인 (Peek)",
                "action_type": "PEEK",
                "highlight_indices": [front] if size > 0 else [],
                "result_text": f"전면(Front, 인덱스 {front})에 위치한 데이터는 [{pk_val}] 입니다.",
                "snapshot": snapshot()
            })

            # Step 6: 42 검색
            found_idx = -1
            found_order = -1
            count_42 = 0
            for i in range(size):
                idx = (front + i) % capacity
                if buffer[idx] == target_search:
                    if found_idx == -1:
                        found_idx = idx
                        found_order = i
                    count_42 += 1

            steps.append({
                "step": 6,
                "title": f"6) 값 '{target_search}'의 위치(Index)와 개수 검색",
                "action_type": "SEARCH",
                "highlight_indices": [found_idx] if found_idx != -1 else [],
                "result_text": (
                    f"값 {target_search}의 인덱스 위치: {found_idx} (Front로부터 {found_order + 1}번째) | 개수: {count_42}개"
                    if found_idx != -1 else f"값 {target_search}을(를) 찾을 수 없습니다."
                ),
                "snapshot": snapshot()
            })

            # Step 7: 88 존재 여부
            exists_88 = any(buffer[(front + i) % capacity] == target_exist for i in range(size))
            hi_88 = []
            if exists_88:
                for i in range(size):
                    idx = (front + i) % capacity
                    if buffer[idx] == target_exist:
                        hi_88.append(idx)

            steps.append({
                "step": 7,
                "title": f"7) 값 '{target_exist}'의 존재 여부 검사",
                "action_type": "CONTAINS",
                "highlight_indices": hi_88,
                "result_text": f"큐 내부에 값 {target_exist}의 존재 여부: {exists_88} ({'존재함 (True)' if exists_88 else '존재하지 않음 (False)'})",
                "snapshot": snapshot()
            })

            # Step 8: 전체 출력
            all_vals = [buffer[(front + i) % capacity] for i in range(size)]
            steps.append({
                "step": 8,
                "title": "8) Front부터 Rear까지 배열 전체 출력",
                "action_type": "DUMP",
                "highlight_indices": [(front + i) % capacity for i in range(size)],
                "result_text": f"Front({front}) -> Rear({(front + size) % capacity}) 전체 데이터 출력: {all_vals}",
                "snapshot": snapshot()
            })

            return jsonify({
                "status": "success",
                "mode": "SCENARIO",
                "steps": steps,
                "final_snapshot": snapshot()
            }), 200

        # 2) 개별 액션 처리
        if action == "init":
            reset_queue(data.get("capacity", 20))
            return jsonify({"status": "success", "message": f"큐 크기를 {capacity}로 초기화했습니다.", "snapshot": snapshot()})

        if action == "push":
            value = data.get("value")
            if value is None:
                return jsonify({"status": "error", "message": "추가할 value가 필요합니다."}), 400
            if size == capacity:
                return jsonify({"status": "error", "message": "큐가 가득 찼습니다(Full).", "snapshot": snapshot()}), 409
            rear = (front + size) % capacity
            buffer[rear] = value
            size += 1
            return jsonify({"status": "success", "message": f"{value}을(를) push했습니다.", "snapshot": snapshot()})

        if action == "PUSH":
            values = data.get("values", [])
            for val in values:
                if size < capacity:
                    rear = (front + size) % capacity
                    buffer[rear] = int(val)
                    size += 1
            return jsonify({"status": "success", "message": "Push 완료", "snapshot": snapshot()})

        if action == "pop" or action == "POP":
            if size == 0:
                return jsonify({"status": "error", "message": "큐가 비어 있습니다(Empty).", "snapshot": snapshot()}), 409
            val = buffer[front]
            buffer[front] = None
            front = (front + 1) % capacity
            size -= 1
            return jsonify({"status": "success", "value": val, "message": f"{val}을(를) pop했습니다.", "snapshot": snapshot()})

        if action == "clear" or action == "CLEAR":
            reset_queue(capacity)
            return jsonify({"status": "success", "message": "큐를 비웠습니다.", "snapshot": snapshot()})

        if action == "find" or action == "SEARCH":
            val = data.get("value", 42)
            found_idx = -1
            count = 0
            for i in range(size):
                idx = (front + i) % capacity
                if buffer[idx] == val:
                    if found_idx == -1:
                        found_idx = idx
                    count += 1
            return jsonify({
                "status": "success",
                "message": f"검색 완료 (존재: {count > 0}, 개수: {count})",
                "highlight_indices": [found_idx] if found_idx != -1 else [],
                "snapshot": snapshot()
            })

        if action == "PEEK":
            val = buffer[front] if size > 0 else None
            return jsonify({
                "status": "success",
                "message": f"전면 데이터: {val}",
                "snapshot": snapshot()
            })

        if action == "SIZE":
            return jsonify({
                "status": "success",
                "message": f"현재 개수: {size}개",
                "snapshot": snapshot()
            })

        if action == "STATUS":
            st = snapshot()["status"]
            return jsonify({
                "status": "success",
                "message": f"상태: {st['state_text']}",
                "snapshot": snapshot()
            })

        if action == "DUMP":
            return jsonify({
                "status": "success",
                "message": "전체 출력 완료",
                "snapshot": snapshot()
            })

        return jsonify({"status": "error", "message": f"지원하지 않는 action입니다: {action}"}), 400

    except (TypeError, ValueError) as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
