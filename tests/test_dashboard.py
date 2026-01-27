import pytest
from unittest.mock import MagicMock, patch
import os
import pandas as pd
from venturalitica.dashboard import render_dashboard

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
        self.selectbox = MagicMock()
        self.multiselect = MagicMock(side_effect=lambda label, options, default=None: default or [])
        self.caption = MagicMock()
        self.text_area = MagicMock(side_effect=lambda label, value=None, **kwargs: value if value is not None else "")
        self.toast = MagicMock()

@pytest.fixture
def mock_st_obj():
    mock = MockStreamlit()
    mock.sidebar.button.return_value = False
    with patch("venturalitica.dashboard.st", mock):
        yield mock

def test_render_dashboard(mock_st_obj, tmp_path):
    with patch("os.getcwd", return_value=str(tmp_path)):
        render_dashboard()
    assert mock_st_obj.title.called

def test_dashboard_scan_flow(mock_st_obj, tmp_path):
    mock_st_obj.sidebar.button.return_value = True
    (tmp_path / "requirements.txt").write_text("pandas==2.1.0")
    
    with patch("os.getcwd", return_value=str(tmp_path)):
        with patch("venturalitica.dashboard.BOMScanner") as mock_scanner:
            mock_scanner_inst = mock_scanner.return_value
            mock_scanner_inst.scan.return_value = '{"components": []}'
            render_dashboard()
    
    assert 'bom' in mock_st_obj.session_state

def test_dashboard_emissions_display(mock_st_obj, tmp_path):
    emissions_csv = tmp_path / "emissions.csv"
    df = pd.DataFrame([{
        'emissions': 0.1,
        'duration': 100,
        'energy_consumed': 0.05
    }])
    df.to_csv(emissions_csv, index=False)
    
    mock_st_obj.sidebar.text_input.return_value = str(tmp_path)
    
    with patch("os.getcwd", return_value=str(tmp_path)):
        render_dashboard()
    
    assert any(call.args == (3,) for call in mock_st_obj.columns.call_args_list)

def test_dashboard_tabs_display(mock_st_obj, tmp_path):
    # Tab 3 logic depends on st.session_state['bom']
    bom_data = {'components': [{'name': 'test-pkg', 'type': 'library'}]}
    mock_st_obj.session_state['bom'] = bom_data
    
    with patch("os.getcwd", return_value=str(tmp_path)):
        render_dashboard()
    
    # "test-pkg" is shown in dataframe, not markdown
    assert mock_st_obj.dataframe.called
    # We could inspect call args but just checking it was called is basic enough
    # Or check if any arg contains the data
    df_arg = mock_st_obj.dataframe.call_args[0][0]
    assert any(d['Library'] == 'test-pkg' for d in df_arg)

def test_dashboard_exceptions(mock_st_obj, tmp_path):
    # Test scan failure
    mock_st_obj.sidebar.button.return_value = True
    with patch("venturalitica.dashboard.BOMScanner", side_effect=Exception("Scan Crash")):
        render_dashboard()
    assert mock_st_obj.sidebar.error.called
    
    # Test emissions read failure
    emissions_csv = tmp_path / "emissions.csv"
    emissions_csv.write_text("corrupt,csv")
    with patch("os.getcwd", return_value=str(tmp_path)):
        render_dashboard()
    assert mock_st_obj.error.called

def test_dashboard_buttons(mock_st_obj, tmp_path):
    # Mocking different buttons returning True
    mock_st_obj.button.return_value = True
    
    # Mock asyncio.run to return a valid tuple (markdown, sections)
    with patch("asyncio.run", return_value=("# Generated Annex", {})):
        with patch("os.getcwd", return_value=str(tmp_path)):
            render_dashboard()
    
    assert mock_st_obj.success.called
    assert mock_st_obj.success.called
