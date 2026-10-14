import os
from enum import Enum
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# 모든 도메인에서의 Cross-Origin 요청 허용
CORS(app, resources={r"/*": {"origins": "*"}})

# 버킷 상태 정의 (미등록, 등록됨, 삭제됨)
class Status(str, Enum):
    EMPTY = "EMPTY"        # 아직 데이터가 한 번도 저장되지 않음
    OCCUPIED = "OCCUPIED"  # 유효한 키/값이 저장되어 있음
    DELETED = "DELETED"    # 데이터가 삭제되어 재사용 가능한 상태

class OpenAddressingHash:
    """
    오픈 어드레싱(선형 탐사법) 기반 해시 테이블 클래스
    """
    def __init__(self, capacity=11, initial_table=None):
        self.capacity = capacity
        if initial_table and len(initial_table) == capacity:
            self.table = initial_table
        else:
            # 초기 빈 테이블 생성
            self.table = [
                {"index": i, "status": Status.EMPTY.value, "key": None, "value": None}
                for i in range(self.capacity)
            ]

    def hash_value(self, key: int) -> int:
        """해시 함수: 제산 잔여법 (Key mod Capacity)"""
        return abs(int(key)) % self.capacity

    def search(self, key: int):
        """키 검색: 충돌 발생 시 다음 버킷을 선형으로 탐사"""
        steps = []
        start_idx = self.hash_value(key)
        steps.append({
            "step": 1,
            "index": start_idx,
            "status": self.table[start_idx]["status"],
            "action": "HASH_START",
            "message": f"해시값 계산 완료: {key} % {self.capacity} = {start_idx}"
        })

        step_count = 1
        for i in range(self.capacity):
            idx = (start_idx + i) % self.capacity
            bucket = self.table[idx]
            step_count += 1

            if bucket["status"] == Status.EMPTY.value:
                steps.append({
                    "step": step_count,
                    "index": idx,
                    "status": bucket["status"],
                    "action": "NOT_FOUND",
                    "message": f"버킷 [{idx}]이 EMPTY이므로 검색 실패 (존재하지 않음)"
                })
                return {"found": False, "index": -1, "steps": steps}

            if bucket["status"] == Status.OCCUPIED.value and bucket["key"] == key:
                steps.append({
                    "step": step_count,
                    "index": idx,
                    "status": bucket["status"],
                    "action": "FOUND",
                    "message": f"버킷 [{idx}]에서 키 {key} 탐색 성공 (값: {bucket['value']})"
                })
                return {"found": True, "index": idx, "value": bucket["value"], "steps": steps}

            steps.append({
                "step": step_count,
                "index": idx,
                "status": bucket["status"],
                "action": "COLLISION_PROBE",
                "message": f"버킷 [{idx}] 불일치({bucket['status']}) -> 다음 버킷으로 선형 탐사 진행"
            })

        steps.append({
            "step": step_count + 1,
            "index": -1,
            "action": "NOT_FOUND",
            "message": "해시 테이블의 모든 버킷을 탐사했으나 키를 찾지 못했습니다."
        })
        return {"found": False, "index": -1, "steps": steps}

    def add(self, key: int, value: str):
        """키/값 추가: 빈 버킷이나 삭제된 버킷에 삽입"""
        steps = []
        start_idx = self.hash_value(key)
        steps.append({
            "step": 1,
            "index": start_idx,
            "status": self.table[start_idx]["status"],
            "action": "HASH_START",
            "message": f"해시값 계산 완료: {key} % {self.capacity} = {start_idx}"
        })

        step_count = 1
        for i in range(self.capacity):
            idx = (start_idx + i) % self.capacity
            bucket = self.table[idx]
            step_count += 1

            # 이미 같은 키가 저장된 경우 갱신
            if bucket["status"] == Status.OCCUPIED.value and bucket["key"] == key:
                bucket["value"] = value
                steps.append({
                    "step": step_count,
                    "index": idx,
                    "status": bucket["status"],
                    "action": "UPDATED",
                    "message": f"버킷 [{idx}]에 동일 키 존재 -> 값을 '{value}'(으)로 갱신"
                })
                return {"success": True, "index": idx, "table": self.table, "steps": steps}

            # 빈 버킷 또는 삭제된 버킷 발견 시 삽입
            if bucket["status"] in (Status.EMPTY.value, Status.DELETED.value):
                bucket["status"] = Status.OCCUPIED.value
                bucket["key"] = key
                bucket["value"] = value
                steps.append({
                    "step": step_count,
                    "index": idx,
                    "status": bucket["status"],
                    "action": "INSERTED",
                    "message": f"버킷 [{idx}]에 신규 키/값 ({key}: {value}) 저장 성공"
                })
                return {"success": True, "index": idx, "table": self.table, "steps": steps}

            steps.append({
                "step": step_count,
                "index": idx,
                "status": bucket["status"],
                "action": "COLLISION_PROBE",
                "message": f"버킷 [{idx}] 점유 중(충돌) -> 다음 버킷으로 이동"
            })

        return {"success": False, "index": -1, "table": self.table, "steps": steps, "message": "해시 테이블이 가득 찼습니다."}

    def remove(self, key: int):
        """키 삭제: 탐색 후 버킷 상태를 DELETED로 변경하여 탐사 경로 유지"""
        search_res = self.search(key)
        steps = search_res["steps"]

        if search_res["found"]:
            idx = search_res["index"]
            self.table[idx]["status"] = Status.DELETED.value
            self.table[idx]["key"] = None
            self.table[idx]["value"] = None
            steps.append({
                "step": len(steps) + 1,
                "index": idx,
                "status": Status.DELETED.value,
                "action": "DELETED",
                "message": f"버킷 [{idx}]의 데이터를 삭제하고 DELETED 상태로 전환"
            })
            return {"success": True, "index": idx, "table": self.table, "steps": steps}

        steps.append({
            "step": len(steps) + 1,
            "index": -1,
            "action": "NOT_FOUND",
            "message": f"키 {key}이 존재하지 않아 삭제에 실패했습니다."
        })
        return {"success": False, "index": -1, "table": self.table, "steps": steps}

    def dump(self):
        """테이블 전체 현황 반환"""
        return {
            "capacity": self.capacity,
            "table": self.table,
            "steps": [{
                "step": 1,
                "index": -1,
                "action": "DUMP",
                "message": f"전체 {self.capacity}개 버킷 현황을 출력합니다."
            }]
        }


@app.route('/hash-operation', methods=['POST'])
@app.route('/', methods=['POST'])
def handle_hash_operation():
    """클라이언트의 연산 요청(init, search, add, remove, dump)을 라우팅"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "요청 본문이 비어 있습니다."}), 400

        action = data.get("action")
        key = data.get("key")
        value = data.get("value")
        current_table = data.get("table")
        capacity = int(data.get("capacity", 11))

        hash_obj = OpenAddressingHash(capacity=capacity, initial_table=current_table)

        if action == "init":
            new_table = OpenAddressingHash(capacity=capacity).table
            return jsonify({
                "status": "success",
                "action": "init",
                "table": new_table,
                "steps": [{"step": 1, "index": -1, "action": "INIT", "message": f"크기 {capacity}의 해시 테이블 초기화 완료"}],
                "complexity": {"time": "O(N)", "space": "O(N)"}
            }), 200

        elif action == "add":
            if key is None:
                return jsonify({"status": "error", "message": "키 값이 필요합니다."}), 400
            res = hash_obj.add(int(key), str(value if value is not None else ""))
            res["action"] = "add"
            res["status"] = "success" if res["success"] else "fail"
            res["complexity"] = {"time": "평균 O(1) / 최악 O(N)", "space": "O(1)"}
            return jsonify(res), 200

        elif action == "search":
            if key is None:
                return jsonify({"status": "error", "message": "검색할 키 값이 필요합니다."}), 400
            res = hash_obj.search(int(key))
            res["action"] = "search"
            res["table"] = hash_obj.table
            res["status"] = "success" if res["found"] else "fail"
            res["complexity"] = {"time": "평균 O(1) / 최악 O(N)", "space": "O(1)"}
            return jsonify(res), 200

        elif action == "remove":
            if key is None:
                return jsonify({"status": "error", "message": "삭제할 키 값이 필요합니다."}), 400
            res = hash_obj.remove(int(key))
            res["action"] = "remove"
            res["status"] = "success" if res["success"] else "fail"
            res["complexity"] = {"time": "평균 O(1) / 최악 O(N)", "space": "O(1)"}
            return jsonify(res), 200

        elif action == "dump":
            res = hash_obj.dump()
            res["action"] = "dump"
            res["status"] = "success"
            res["complexity"] = {"time": "O(N)", "space": "O(1)"}
            return jsonify(res), 200

        else:
            return jsonify({"status": "error", "message": f"알 수 없는 액션: {action}"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
