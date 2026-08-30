"""LangGraph 编排图。

本期为最简结构：START -> model -> END。
State 用 MessagesState（内置 add_messages reducer），后续扩展多 Agent / 工具时
只需在此插入节点，视图层无需改动。
"""

from langgraph.graph import END, START, MessagesState, StateGraph

from .llm import get_llm


def _call_model(state: MessagesState) -> dict:
    response = get_llm().invoke(state['messages'])
    return {'messages': [response]}


def build_graph():
    builder = StateGraph(MessagesState)
    builder.add_node('model', _call_model)
    builder.add_edge(START, 'model')
    builder.add_edge('model', END)
    return builder.compile()


# 模块级单例图
graph = build_graph()
