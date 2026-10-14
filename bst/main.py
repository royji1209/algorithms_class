import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# 모든 도메인에서의 Cross-Origin 요청 허용
CORS(app, resources={r"/*": {"origins": "*"}})


class Node:
    """이진 검색 트리의 개별 노드를 표현하는 클래스"""
    def __init__(self, key: int, value: str, left=None, right=None):
        self.key = int(key)
        self.value = str(value)
        self.left = left    # 왼쪽 자식 노드 참조 (Node 객체)
        self.right = right  # 오른쪽 자식 노드 참조 (Node 객체)

    def to_dict(self):
        """노드 및 하위 서브트리를 JSON 직렬화 가능한 딕셔너리로 변환"""
        return {
            "key": self.key,
            "value": self.value,
            "left": self.left.to_dict() if self.left else None,
            "right": self.right.to_dict() if self.right else None
        }

    @staticmethod
    def from_dict(data):
        """클라이언트가 전달한 딕셔너리를 Node 객체 트리로 역직렬화"""
        if not data:
            return None
        node = Node(data["key"], data.get("value", ""))
        node.left = Node.from_dict(data.get("left"))
        node.right = Node.from_dict(data.get("right"))
        return node


class BinarySearchTree:
    """이진 검색 트리 연산(탐색, 삽입, 삭제, 순회 등)을 수행하는 클래스"""
    def __init__(self, root=None):
        self.root = root

    def search(self, key: int):
        """키 검색: BST 속성에 따라 좌/우 서브트리로 분기 탐색"""
        steps = []
        curr = self.root
        step_num = 0

        while curr:
            step_num += 1
            if key == curr.key:
                steps.append({
                    "step": step_num,
                    "node_key": curr.key,
                    "action": "FOUND",
                    "message": f"노드 [{curr.key}] 일치: 목표값(Key={key})을 발견했습니다! (값: '{curr.value}')"
                })
                return {"found": True, "value": curr.value, "steps": steps}
            elif key < curr.key:
                steps.append({
                    "step": step_num,
                    "node_key": curr.key,
                    "action": "GO_LEFT",
                    "message": f"{key} < {curr.key} 이므로 왼쪽 서브트리로 이동합니다."
                })
                curr = curr.left
            else:
                steps.append({
                    "step": step_num,
                    "node_key": curr.key,
                    "action": "GO_RIGHT",
                    "message": f"{key} > {curr.key} 이므로 오른쪽 서브트리로 이동합니다."
                })
                curr = curr.right

        steps.append({
            "step": step_num + 1,
            "node_key": None,
            "action": "NOT_FOUND",
            "message": f"탐색 경로의 끝(None)에 도달했습니다. 키 {key}가 트리에 존재하지 않습니다."
        })
        return {"found": False, "value": None, "steps": steps}

    def add(self, key: int, value: str):
        """노드 삽입: 중복 키는 값을 갱신하고, 없으면 리프 위치에 추가"""
        steps = []
        if not self.root:
            self.root = Node(key, value)
            steps.append({
                "step": 1,
                "node_key": key,
                "action": "INSERTED",
                "message": f"트리가 비어 있으므로 [{key}: '{value}'] 노드를 루트로 삽입했습니다."
            })
            return {"success": True, "steps": steps, "tree": self.root.to_dict()}

        curr = self.root
        step_num = 0
        while True:
            step_num += 1
            if key == curr.key:
                curr.value = value
                steps.append({
                    "step": step_num,
                    "node_key": curr.key,
                    "action": "UPDATED",
                    "message": f"동일한 키 [{key}]가 이미 존재하므로 값을 '{value}'(으)로 갱신했습니다."
                })
                return {"success": True, "steps": steps, "tree": self.root.to_dict()}
            elif key < curr.key:
                steps.append({
                    "step": step_num,
                    "node_key": curr.key,
                    "action": "GO_LEFT",
                    "message": f"{key} < {curr.key} 이므로 왼쪽으로 이동합니다."
                })
                if not curr.left:
                    curr.left = Node(key, value)
                    steps.append({
                        "step": step_num + 1,
                        "node_key": key,
                        "action": "INSERTED",
                        "message": f"노드 [{curr.key}]의 왼쪽 자식으로 신규 노드 [{key}: '{value}']를 삽입했습니다."
                    })
                    return {"success": True, "steps": steps, "tree": self.root.to_dict()}
                curr = curr.left
            else:
                steps.append({
                    "step": step_num,
                    "node_key": curr.key,
                    "action": "GO_RIGHT",
                    "message": f"{key} > {curr.key} 이므로 오른쪽으로 이동합니다."
                })
                if not curr.right:
                    curr.right = Node(key, value)
                    steps.append({
                        "step": step_num + 1,
                        "node_key": key,
                        "action": "INSERTED",
                        "message": f"노드 [{curr.key}]의 오른쪽 자식으로 신규 노드 [{key}: '{value}']를 삽입했습니다."
                    })
                    return {"success": True, "steps": steps, "tree": self.root.to_dict()}
                curr = curr.right

    def remove(self, key: int):
        """노드 삭제: 1) 자식 없음, 2) 자식 1개, 3) 자식 2개(오른쪽 최소 노드로 대체) 처리"""
        steps = []
        step_num = [0]  # 참조형 변수로 단계 번호 누적 관리

        def _remove_recursive(node, k):
            if not node:
                step_num[0] += 1
                steps.append({
                    "step": step_num[0],
                    "node_key": None,
                    "action": "NOT_FOUND",
                    "message": f"키 {k}를 찾지 못하여 삭제에 실패했습니다."
                })
                return None, False

            step_num[0] += 1
            if k < node.key:
                steps.append({
                    "step": step_num[0],
                    "node_key": node.key,
                    "action": "GO_LEFT",
                    "message": f"{k} < {node.key} 이므로 왼쪽 서브트리에서 삭제 대상 탐색"
                })
                node.left, deleted = _remove_recursive(node.left, k)
                return node, deleted
            elif k > node.key:
                steps.append({
                    "step": step_num[0],
                    "node_key": node.key,
                    "action": "GO_RIGHT",
                    "message": f"{k} > {node.key} 이므로 오른쪽 서브트리에서 삭제 대상 탐색"
                })
                node.right, deleted = _remove_recursive(node.right, k)
                return node, deleted
            else:
                # 삭제 대상 노드 발견
                steps.append({
                    "step": step_num[0],
                    "node_key": node.key,
                    "action": "TARGET_FOUND",
                    "message": f"삭제 대상 노드 [{node.key}]를 발견했습니다."
                })

                # 경우 1 & 2: 자식이 없거나 하나뿐인 경우
                if not node.left:
                    step_num[0] += 1
                    steps.append({
                        "step": step_num[0],
                        "node_key": node.key,
                        "action": "DELETED",
                        "message": f"노드 [{node.key}]를 오른쪽 서브트리로 대체/삭제합니다."
                    })
                    return node.right, True
                elif not node.right:
                    step_num[0] += 1
                    steps.append({
                        "step": step_num[0],
                        "node_key": node.key,
                        "action": "DELETED",
                        "message": f"노드 [{node.key}]를 왼쪽 서브트리로 대체/삭제합니다."
                    })
                    return node.left, True

                # 경우 3: 자식이 둘 다 있는 경우 -> 오른쪽 서브트리의 최솟값(후계자)으로 대체
                successor = node.right
                while successor.left:
                    successor = successor.left

                step_num[0] += 1
                steps.append({
                    "step": step_num[0],
                    "node_key": successor.key,
                    "action": "SUCCESSOR_FOUND",
                    "message": f"자식이 2개이므로 오른쪽 서브트리의 최솟값 노드 [{successor.key}]를 후계자로 선택합니다."
                })

                node.key = successor.key
                node.value = successor.value
                node.right, _ = _remove_recursive(node.right, successor.key)
                return node, True

        self.root, is_deleted = _remove_recursive(self.root, key)
        return {
            "success": is_deleted,
            "steps": steps,
            "tree": self.root.to_dict() if self.root else None
        }

    def dump(self):
        """중위 순회(Inorder Traversal)를 수행하여 키를 오름차순으로 덤프"""
        inorder_nodes = []
        steps = []
        step_counter = [0]

        def _inorder(node):
            if not node:
                return
            _inorder(node.left)
            step_counter[0] += 1
            inorder_nodes.append({"key": node.key, "value": node.value})
            steps.append({
                "step": step_counter[0],
                "node_key": node.key,
                "action": "DUMP_VISIT",
                "message": f"중위 순회 방문: [{node.key}: '{node.value}']"
            })
            _inorder(node.right)

        _inorder(self.root)
        return {
            "inorder": inorder_nodes,
            "steps": steps,
            "message": f"총 {len(inorder_nodes)}개 노드가 오름차순으로 덤프되었습니다."
        }

    def min_key(self):
        """최솟값 검색: 루트부터 왼쪽 끝까지 탐색"""
        if not self.root:
            return {"found": False, "key": None, "steps": []}

        steps = []
        curr = self.root
        step_num = 0
        while curr.left:
            step_num += 1
            steps.append({
                "step": step_num,
                "node_key": curr.key,
                "action": "GO_LEFT",
                "message": f"더 작은 값을 찾아 [{curr.key}]의 왼쪽 자식으로 이동"
            })
            curr = curr.left

        step_num += 1
        steps.append({
            "step": step_num,
            "node_key": curr.key,
            "action": "MIN_FOUND",
            "message": f"트리의 최소 키 노드 [{curr.key}: '{curr.value}'] 발견!"
        })
        return {"found": True, "key": curr.key, "value": curr.value, "steps": steps}

    def max_key(self):
        """최댓값 검색: 루트부터 오른쪽 끝까지 탐색"""
        if not self.root:
            return {"found": False, "key": None, "steps": []}

        steps = []
        curr = self.root
        step_num = 0
        while curr.right:
            step_num += 1
            steps.append({
                "step": step_num,
                "node_key": curr.key,
                "action": "GO_RIGHT",
                "message": f"더 큰 값을 찾아 [{curr.key}]의 오른쪽 자식으로 이동"
            })
            curr = curr.right

        step_num += 1
        steps.append({
            "step": step_num,
            "node_key": curr.key,
            "action": "MAX_FOUND",
            "message": f"트리의 최대 키 노드 [{curr.key}: '{curr.value}'] 발견!"
        })
        return {"found": True, "key": curr.key, "value": curr.value, "steps": steps}


@app.route('/bst-operation', methods=['POST'])
@app.route('/', methods=['POST'])
def handle_bst():
    """클라이언트로부터 트리 상태와 수행할 연산을 받아 실행 후 결과 반환"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "요청 JSON이 비어 있습니다."}), 400

        action = data.get("action")
        key = data.get("key")
        value = data.get("value", "")
        tree_dict = data.get("tree")

        # 클라이언트의 트리 상태 복원
        root_node = Node.from_dict(tree_dict)
        bst = BinarySearchTree(root=root_node)

        # 1. 초기화 (Init)
        if action == "init":
            return jsonify({
                "status": "success",
                "action": "init",
                "tree": None,
                "steps": [{"step": 1, "node_key": None, "action": "INIT", "message": "트리를 초기화했습니다."}],
                "complexity": {"time": "O(1)", "space": "O(1)"}
            }), 200

        # 2. 삽입 (Add)
        elif action == "add":
            if key is None:
                return jsonify({"status": "error", "message": "삽입할 키 값이 누락되었습니다."}), 400
            res = bst.add(int(key), str(value))
            res["action"] = "add"
            res["status"] = "success"
            res["complexity"] = {"time": "평균 O(log N) / 최악 O(N)", "space": "O(1)"}
            return jsonify(res), 200

        # 3. 검색 (Search)
        elif action == "search":
            if key is None:
                return jsonify({"status": "error", "message": "검색할 키 값이 누락되었습니다."}), 400
            res = bst.search(int(key))
            res["action"] = "search"
            res["tree"] = bst.root.to_dict() if bst.root else None
            res["status"] = "success" if res["found"] else "fail"
            res["complexity"] = {"time": "평균 O(log N) / 최악 O(N)", "space": "O(1)"}
            return jsonify(res), 200

        # 4. 삭제 (Remove)
        elif action == "remove":
            if key is None:
                return jsonify({"status": "error", "message": "삭제할 키 값이 누락되었습니다."}), 400
            res = bst.remove(int(key))
            res["action"] = "remove"
            res["status"] = "success" if res["success"] else "fail"
            res["complexity"] = {"time": "평균 O(log N) / 최악 O(N)", "space": "O(N)"}
            return jsonify(res), 200

        # 5. 덤프 (Dump - 중위 순회)
        elif action == "dump":
            res = bst.dump()
            res["action"] = "dump"
            res["tree"] = bst.root.to_dict() if bst.root else None
            res["status"] = "success"
            res["complexity"] = {"time": "O(N)", "space": "O(N)"}
            return jsonify(res), 200

        # 6. 키의 범위 (Min & Max Key 동시 조회)
        elif action == "range":
            min_res = bst.min_key()
            max_res = bst.max_key()

            # 단계 합치기
            combined_steps = []
            for s in min_res["steps"]:
                s_copy = s.copy()
                s_copy["message"] = "[최솟값 탐색] " + s_copy["message"]
                combined_steps.append(s_copy)
            for s in max_res["steps"]:
                s_copy = s.copy()
                s_copy["step"] = len(combined_steps) + 1
                s_copy["message"] = "[최댓값 탐색] " + s_copy["message"]
                combined_steps.append(s_copy)

            return jsonify({
                "status": "success",
                "action": "range",
                "min_key": min_res.get("key"),
                "max_key": max_res.get("key"),
                "steps": combined_steps,
                "tree": bst.root.to_dict() if bst.root else None,
                "complexity": {"time": "평균 O(log N) / 최악 O(N)", "space": "O(1)"}
            }), 200

        else:
            return jsonify({"status": "error", "message": f"알 수 없는 연산입니다: {action}"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
