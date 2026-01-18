from typing import TypedDict, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END

# ------------------------------------------------------------------------------
# 1. State Definition (상태 정의)
# ------------------------------------------------------------------------------
# English: This dictionary acts as the "Memory" of our agent.
# It passes data between different steps (nodes).
# Korean: 이 딕셔너리는 에이전트의 "기억(메모리)" 역할을 합니다.
# 각 단계(노드) 사이에서 데이터를 주고받는 바구니입니다.
class AgentState(TypedDict):
    query: str                # User input (사용자 질문/텍스트)
    analysis_result: dict     # AI Analysis output (AI 분석 결과)

# ------------------------------------------------------------------------------
# 2. Node Functions (노드 함수)
# ------------------------------------------------------------------------------
# English: This function represents a single step in the workflow.
# Currently, it is a MOCK function for testing infrastructure.
# Korean: 이 함수는 작업 흐름의 한 단계를 의미합니다.
# 현재는 인프라 테스트를 위해 가짜(Mock) 응답을 주는 로직입니다.
def analyze_node(state: AgentState):
    user_query = state['query']
    
    # Simple logic for testing (테스트용 단순 로직)
    # Later, we will connect OpenAI here. (나중에 여기에 OpenAI를 연결합니다.)
    print(f"Processing query: {user_query}")
    
    return {
        "analysis_result": {
            "ticker": "UNKNOWN",
            "decision": "HOLD",
            "reason": f"Analysis complete for: {user_query}"
        }
    }

# ------------------------------------------------------------------------------
# 3. Graph Construction (그래프 조립)
# ------------------------------------------------------------------------------
# English: We connect the nodes to create a workflow.
# Korean: 노드들을 연결하여 작업 흐름을 만듭니다.
workflow = StateGraph(AgentState)

# Add the analysis node (분석 노드 추가)
workflow.add_node("analyst", analyze_node)

# Set the entry point (시작점 설정)
workflow.set_entry_point("analyst")

# End the graph after analysis (분석 후 종료)
workflow.add_edge("analyst", END)

# Compile the graph into a runnable application
# 그래프를 실행 가능한 앱으로 컴파일합니다.
agent_app = workflow.compile()