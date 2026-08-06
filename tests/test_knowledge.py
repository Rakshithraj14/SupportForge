from pathlib import Path
from unittest.mock import MagicMock, patch


def test_upload_markdown_document_enqueues_ingestion(client):
    with patch("app.api.knowledge.ingest_document_task", new=MagicMock()) as mock_task:
        files = {"file": ("notes.md", b"# Hello\n\nSome support content.", "text/markdown")}
        response = client.post("/knowledge/upload", files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "notes.md"
    assert body["status"] == "pending"
    assert body["chunk_count"] is None

    mock_task.delay.assert_called_once()
    args = mock_task.delay.call_args.args
    assert args[0] == body["document_id"]
    assert args[1] == "notes.md"
    assert Path(args[2]).exists()
    Path(args[2]).unlink()


def test_upload_unsupported_file_type_fails(client):
    files = {"file": ("data.exe", b"binary content", "application/octet-stream")}
    response = client.post("/knowledge/upload", files=files)

    assert response.status_code == 400
