from unittest.mock import AsyncMock, patch


def _fake_workflow(answer: str) -> AsyncMock:
    workflow = AsyncMock()
    workflow.ainvoke.return_value = {"question": "", "context": [], "answer": answer}
    return workflow


def test_chat_returns_answer(client):
    with patch(
        "app.services.chat_service.get_workflow",
        return_value=_fake_workflow("Hello! How can I help?"),
    ):
        response = client.post("/chat", json={"chat_id": "chat-1", "message": "hi"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Hello! How can I help?"
    assert "conversation_id" in body
    assert "message_id" in body


def test_chat_reuses_conversation_for_same_chat_id(client):
    with patch(
        "app.services.chat_service.get_workflow",
        return_value=_fake_workflow("some answer"),
    ):
        first = client.post("/chat", json={"chat_id": "chat-2", "message": "hi"})
        second = client.post("/chat", json={"chat_id": "chat-2", "message": "again"})

    assert first.json()["conversation_id"] == second.json()["conversation_id"]
    assert first.json()["message_id"] != second.json()["message_id"]
