import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Cross-Origin Resource Sharing (CORS) 전체 도메인 허용 설정
# 실제 운영 환경에서는 특정 도메인(GAS 도메인 등)으로 제한할 수 있습니다.
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/binary-search', methods=['POST'])
def binary_search():
    """
    이진 검색 알고리즘 수행 및 단계별 상태 반환 엔드포인트
    Request Body:
        {
            "array": [1, 3, 5, 7, 9, 11, 13, 15],
            "target": 7
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "요청 본문(JSON)이 비어 있습니다."}), 400

        raw_array = data.get("array", [])
        target = data.get("target")

        if target is None:
            return jsonify({"error": "'target' 값이 전달되지 않았습니다."}), 400

        # 이진 검색을 위한 사전 정렬 보장
        sorted_array = sorted([int(x) for x in raw_array])
        target = int(target)

        steps = []
        left = 0
        right = len(sorted_array) - 1
        found_index = -1
        step_number = 0

        # 이진 검색 루프 시작
        while left <= right:
            step_number += 1
            mid = (left + right) // 2
            mid_val = sorted_array[mid]

            step_data = {
                "step": step_number,
                "left": left,
                "right": right,
                "mid": mid,
                "mid_val": mid_val,
                "target": target,
                "action": ""
            }

            if mid_val == target:
                step_data["action"] = "FOUND"
                steps.append(step_data)
                found_index = mid
                break
            elif mid_val < target:
                step_data["action"] = "MOVE_RIGHT"  # 타겟이 더 크므로 우측 탐색 (left 조정)
                steps.append(step_data)
                left = mid + 1
            else:
                step_data["action"] = "MOVE_LEFT"   # 타겟이 더 작으므로 좌측 탐색 (right 조정)
                steps.append(step_data)
                right = mid - 1

        # 검색 실패 시 추가 기록
        if found_index == -1 and left > right:
            steps.append({
                "step": step_number + 1,
                "left": left,
                "right": right,
                "mid": None,
                "mid_val": None,
                "target": target,
                "action": "NOT_FOUND"
            })

        return jsonify({
            "status": "success",
            "array": sorted_array,
            "target": target,
            "found_index": found_index,
            "total_steps": len(steps),
            "steps": steps,
            "complexity": {
                "time_complexity": "O(log N)",
                "space_complexity": "O(1)"
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """서버 상태 확인용 엔드포인트"""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    # Cloud Run 환경변수 PORT(기본값 8080) 수신
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
