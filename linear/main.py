import os
from typing import List, Dict, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# 외부 호출 허용 (GAS 등에서 접근 가능하도록 CORS 활성화)
CORS(app)


# ==========================================
# 1. 자료구조 및 알고리즘 모듈 (객체지향 설계)
# ==========================================
class ElementNode:
    """배열 내의 각 요소와 메타데이터를 캡슐화한 노드 클래스"""
    def __init__(self, index: int, value: Any):
        self._index = index
        self._value = value

    @property
    def index(self) -> int:
        return self._index

    @property
    def value(self) -> Any:
        return self._value


class LinearSearchController:
    """
    선형 검색(Linear Search)의 수행 및 단계별 추적(Trace)을 전담하는 컨트롤러
    - 시간 복잡도: 
        * 최선의 경우: O(1) (첫 번째 요소가 타깃일 때)
        * 최악의 경우: O(N) (배열 끝에 있거나 존재하지 않을 때)
        * 평균: O(N)
    - 공간 복잡도: O(N) (단계별 추적 로그 보관용)
    """
    def __init__(self, data: List[Any]):
        # 외부 입력 배열을 ElementNode 객체 리스트로 캡슐화
        self._nodes: List[ElementNode] = [ElementNode(idx, val) for idx, val in enumerate(data)]
        self._history: List[Dict[str, Any]] = []

    def search(self, target: Any) -> Dict[str, Any]:
        """
        타깃 요소를 선형 탐색하며, 각 탐색 단계를 히스토리에 기록
        """
        self._history.clear()
        found_index: int = -1

        for node in self._nodes:
            is_matched = (node.value == target)
            
            # 각 비교 단계의 스냅샷 생성
            step_record = {
                "step": len(self._history) + 1,
                "current_index": node.index,
                "current_value": node.value,
                "target": target,
                "matched": is_matched,
                "description": f"인덱스 {node.index} (값: {node.value})과 목표값 {target} 비교 -> {'일치' if is_matched else '불일치'}"
            }
            self._history.append(step_record)

            if is_matched:
                found_index = node.index
                break  # 타깃을 찾았으므로 즉시 종료

        return {
            "found": (found_index != -1),
            "target_index": found_index,
            "total_comparisons": len(self._history),
            "complexity": {
                "time_best": "O(1)",
                "time_worst": "O(N)",
                "time_average": "O(N)",
                "space": "O(1) (알고리즘 자체 기준)"
            },
            "steps": self._history
        }


# ==========================================
# 2. HTTP 라우트 핸들러
# ==========================================
@app.route("/", methods=["GET"])
def health_check():
    """서버 상태 헬스체크 엔드포인트"""
    return jsonify({"status": "healthy", "service": "Cloud Run Linear Search API"}), 200


@app.route("/search", methods=["POST"])
def execute_search():
    """
    선형 검색 수행 요청 API
    Request Body:
        {
            "array": [10, 20, 30, 40, 50],
            "target": 30
        }
    """
    try:
        req_data = request.get_json(silent=True)
        if not req_data:
            return jsonify({"status": "error", "message": "유효한 JSON 요청 본문이 필요합니다."}), 400

        array_data = req_data.get("array")
        target_val = req_data.get("target")

        # 엣지 케이스 방어 로직
        if array_data is None or target_val is None:
            return jsonify({"status": "error", "message": "'array'와 'target' 필드는 필수 항목입니다."}), 400

        if not isinstance(array_data, list):
            return jsonify({"status": "error", "message": "'array'는 리스트 형태여야 합니다."}), 400

        if len(array_data) == 0:
            return jsonify({
                "status": "success",
                "result": {
                    "found": False,
                    "target_index": -1,
                    "total_comparisons": 0,
                    "complexity": {"time": "O(1)", "space": "O(1)"},
                    "steps": [],
                    "message": "빈 배열이 제공되어 검색을 즉시 종료했습니다."
                }
            }), 200

        # 알고리즘 컨트롤러 인스턴스 생성 및 검색 수행
        controller = LinearSearchController(array_data)
        search_result = controller.search(target_val)

        return jsonify({
            "status": "success",
            "data": search_result
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"서버 내부 오류: {str(e)}"}), 500


if __name__ == "__main__":
    # 로컬 디버깅 및 Cloud Run 환경 변수 포트 바인딩
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
