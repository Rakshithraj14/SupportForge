from unittest.mock import AsyncMock, patch


def test_upload_markdown_document(client):
    with (
        patch(
            "app.services.knowledge_service.embed_chunks",
            new=AsyncMock(return_value=[[0.1] * 768]),
        ),
        patch("app.services.knowledge_service.index_chunks", new=AsyncMock()),
    ):
        files = {"file": ("notes.md", b"# Hello\n\nSome support content.", "text/markdown")}
        response = client.post("/knowledge/upload", files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "notes.md"
    assert body["status"] == "indexed"
    assert body["chunk_count"] == 1


def test_upload_unsupported_file_type_fails(client):
    files = {"file": ("data.exe", b"binary content", "application/octet-stream")}
    response = client.post("/knowledge/upload", files=files)

    assert response.status_code == 400
