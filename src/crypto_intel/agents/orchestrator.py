from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from crypto_intel.agents.market_data_agent import market_data_agent
from crypto_intel.agents.report_agent import report_agent
from crypto_intel.agents.sentiment_agent import sentiment_agent
from crypto_intel.agents.state import AnalysisState
from crypto_intel.agents.technical_agent import technical_agent


def build_graph() -> StateGraph:
    graph = StateGraph(AnalysisState)

    graph.add_node("market_data", market_data_agent)
    graph.add_node("technical", technical_agent)
    graph.add_node("sentiment", sentiment_agent)
    graph.add_node("report", report_agent)

    graph.set_entry_point("market_data")

    graph.add_edge("market_data", "technical")
    graph.add_edge("market_data", "sentiment")
    graph.add_edge("technical", "report")
    graph.add_edge("sentiment", "report")
    graph.add_edge("report", END)

    return graph


async def run_analysis(token: str) -> dict[str, Any]:
    graph = build_graph()
    app = graph.compile()

    initial_state: AnalysisState = {
        "token": token,
        "token_id": "",
        "price_data": {},
        "price_history": [],
        "technical_indicators": {},
        "news_articles": [],
        "sentiment_score": 0.0,
        "relevant_context": [],
        "analysis_summary": "",
        "risk_level": "medium",
        "confidence": 0.5,
    }

    result = await app.ainvoke(initial_state)
    return dict(result)
