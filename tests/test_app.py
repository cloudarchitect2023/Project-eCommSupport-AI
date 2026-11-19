from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_frontend_renders_without_external_services():
    app = Path(__file__).resolve().parents[1] / "frontend" / "app.py"
    result = AppTest.from_file(str(app)).run()
    assert not result.exception
    assert any("eCommSupport AI" in title.value for title in result.title)
    assert result.chat_input
