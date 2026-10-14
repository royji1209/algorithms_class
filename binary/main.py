import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/binary-search', methods=['POST'])
def binary_search():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "요청 본문이 비어 있습니다."}), 400

        raw_array = data.get("array", [])
        target = data.get("target")

        if target is None:
            return jsonify({"error": "'target' 값이 전달되지 않았습니다."}), 400

        sorted_array = sorted([int(x) for x in raw_array])
        target = int(target)

        steps = []
        left = 0
        right = len(sorted_array) - 1
        found_index = -1
        step_number = 0

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
                step_data["action"] = "MOVE_RIGHT"
                steps.append(step_data)
                left = mid + 1
            else:
                step_data["action"] = "MOVE_LEFT"
                steps.append(step_data)
                right = mid - 1

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
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
