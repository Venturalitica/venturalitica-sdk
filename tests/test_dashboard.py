from unittest.mock import MagicMock, patch

import pytest

from venturalitica.dashboard.main import render_dashboard


class MockStreamlit:
    def __init__(self):
        self.sidebar = MagicMock()
        self.sidebar.text_input = MagicMock(side_effect=lambda label, value=None: value)
        self.session_state = {}
        self.tabs = MagicMock(return_value=[MagicMock() for _ in range(5)])
        self.columns = MagicMock(side_effect=lambda n: [MagicMock() for _ in range(len(n) if isinstance(n, list) else n)])
        self.title = MagicMock()
        self.header = MagicMock()
        self.info = MagicMock()
        self.warning = MagicMock()
        self.subheader = MagicMock()
        self.json = MagicMock()
        self.divider = MagicMock()
        self.success = MagicMock()
        self.error = MagicMock()
        self.code = MagicMock()
        self.markdown = MagicMock()
        self.text = MagicMock()
        self.button = MagicMock(return_value=False)
        self.spinner = MagicMock()
        self.spinner.return_value.__enter__ = MagicMock()
        self.spinner.return_value.__exit__ = MagicMock()
        self.toast = MagicMock()
        self.balloons = MagicMock()
        self.image = MagicMock()
        self.expander = MagicMock()
        self.expander.return_value.__enter__ = MagicMock()
        self.expander.return_value.__exit__ = MagicMock()
        self.dataframe = MagicMock()
        self.container = MagicMock()
        self.container.return_value.__enter__ = MagicMock()
        self.container.return_value.__exit__ = MagicMock()
        self.selectbox = MagicMock(side_effect=lambda label, options, index=0, **kwargs: options[index] if options else None)
        self.multiselect = MagicMock(side_effect=lambda label, options, default=None: default or [])
        self.caption = MagicMock()
        self.text_area = MagicMock(side_effect=lambda label, value=None, **kwargs: value if value is not None else "")
        self.toast = MagicMock()
        self.radio = MagicMock(side_effect=lambda label, options, index=0, **kwargs: options[index] if options else None)
        self.text_input = MagicMock(side_effect=lambda label, value="", type="default", help="": value)
        
        # Connect sidebar mocks
        self.sidebar.radio = self.radio
        self.sidebar.selectbox = self.selectbox
        self.sidebar.multiselect = self.multiselect
        self.sidebar.text_input = self.text_input
        self.sidebar.button = self.button

@pytest.fixture
def mock_st_obj():
    mock = MockStreamlit()
    mock.sidebar.button.return_value = False
    with patch("venturalitica.dashboard.main.st", mock):
        yield mock

def test_render_dashboard(mock_st_obj, tmp_path):
    with patch("os.getcwd", return_value=str(tmp_path)):
        render_dashboard()
    assert mock_st_obj.markdown.called

def test_dashboard_context_loading(mock_st_obj, tmp_path):
    # Test that context loading attempts to read file
    (tmp_path / "system_description.yaml").touch()
    with patch("os.getcwd", return_value=str(tmp_path)):
        render_dashboard()
    # Check that sidebar radio was called (it means phases were loaded)
    assert mock_st_obj.sidebar.radio.called

