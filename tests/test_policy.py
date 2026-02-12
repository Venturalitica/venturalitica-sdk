"""
Comprehensive tests for venturalitica.policy module.
Covers PolicyManager: load, save, validate, get_schema.
"""


import pytest
import yaml

from venturalitica.policy import POLICY_SCHEMA, PolicyManager

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def pm(tmp_path):
    """PolicyManager pointing at a fresh tmp directory."""
    return PolicyManager(str(tmp_path))


def _valid_policy():
    return {
        "title": "Test Policy",
        "controls": [
            {
                "id": "C1",
                "metric_key": "demographic_parity_diff",
                "operator": "<=",
                "threshold": 0.1,
                "severity": "high",
                "description": "Demographic parity must be below 0.1",
            }
        ],
    }


# ===========================================================================
# load()
# ===========================================================================


class TestLoad:
    def test_load_file_does_not_exist(self, pm):
        """When the policy file doesn't exist, load() returns default dict."""
        data = pm.load()
        assert data == {"title": "New Policy", "controls": []}

    def test_load_valid_dict_policy(self, pm):
        """load() returns the dict stored in YAML."""
        policy = _valid_policy()
        pm.policy_path.parent.mkdir(parents=True, exist_ok=True)
        with open(pm.policy_path, "w") as f:
            yaml.dump(policy, f)

        loaded = pm.load()
        assert loaded["title"] == "Test Policy"
        assert len(loaded["controls"]) == 1
        assert loaded["controls"][0]["id"] == "C1"

    def test_load_legacy_list_format(self, pm):
        """A YAML file containing a bare list is wrapped in a dict."""
        controls = [
            {"id": "L1", "metric_key": "k_anonymity", "operator": ">=", "threshold": 5}
        ]
        pm.policy_path.parent.mkdir(parents=True, exist_ok=True)
        with open(pm.policy_path, "w") as f:
            yaml.dump(controls, f)

        loaded = pm.load()
        assert loaded["title"] == "Legacy Policy"
        assert loaded["controls"] == controls

    def test_load_empty_yaml(self, pm):
        """An empty YAML file (safe_load returns None) produces default dict."""
        pm.policy_path.parent.mkdir(parents=True, exist_ok=True)
        pm.policy_path.write_text("")

        loaded = pm.load()
        # yaml.safe_load("") returns None -> `or {}` -> isinstance({}, list) is False -> returns {}
        assert loaded == {}

    def test_load_yaml_with_only_whitespace(self, pm):
        """Whitespace-only YAML also returns empty dict."""
        pm.policy_path.parent.mkdir(parents=True, exist_ok=True)
        pm.policy_path.write_text("   \n\n")

        loaded = pm.load()
        assert loaded == {}


# ===========================================================================
# save()
# ===========================================================================


class TestSave:
    def test_save_valid_data(self, pm):
        """save() writes YAML to disk and returns True."""
        pm.policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy = _valid_policy()

        result = pm.save(policy)
        assert result is True
        assert pm.policy_path.exists()

        with open(pm.policy_path, "r") as f:
            on_disk = yaml.safe_load(f)
        assert on_disk["title"] == "Test Policy"
        assert len(on_disk["controls"]) == 1

    def test_save_missing_title_raises(self, pm):
        """save() raises ValueError when 'title' is missing or falsy."""
        pm.policy_path.parent.mkdir(parents=True, exist_ok=True)
        with pytest.raises(ValueError, match="Policy title is required"):
            pm.save({"controls": []})

    def test_save_empty_title_raises(self, pm):
        """save() raises ValueError when title is empty string."""
        pm.policy_path.parent.mkdir(parents=True, exist_ok=True)
        with pytest.raises(ValueError, match="Policy title is required"):
            pm.save({"title": "", "controls": []})

    def test_save_roundtrip(self, pm):
        """Data saved can be loaded back identically."""
        pm.policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy = _valid_policy()
        pm.save(policy)
        loaded = pm.load()
        assert loaded["title"] == policy["title"]
        assert loaded["controls"] == policy["controls"]


# ===========================================================================
# validate()
# ===========================================================================


class TestValidate:
    def test_validate_valid_data(self, pm):
        """Fully valid policy yields empty error list."""
        errors = pm.validate(_valid_policy())
        assert errors == []

    def test_validate_missing_title(self, pm):
        errors = pm.validate({"controls": []})
        assert any("title" in e for e in errors)

    def test_validate_missing_controls_key(self, pm):
        errors = pm.validate({"title": "No controls"})
        assert any("controls" in e for e in errors)

    def test_validate_controls_not_a_list(self, pm):
        errors = pm.validate({"title": "Bad", "controls": "not_a_list"})
        assert any("controls" in e for e in errors)

    def test_validate_control_missing_id(self, pm):
        policy = {
            "title": "Partial",
            "controls": [{"metric_key": "x", "operator": ">", "threshold": 0.5}],
        }
        errors = pm.validate(policy)
        assert any("id" in e for e in errors)

    def test_validate_control_missing_metric_key(self, pm):
        policy = {
            "title": "Partial",
            "controls": [{"id": "C1", "operator": ">", "threshold": 0.5}],
        }
        errors = pm.validate(policy)
        assert any("metric_key" in e for e in errors)

    def test_validate_control_missing_operator(self, pm):
        policy = {
            "title": "Partial",
            "controls": [{"id": "C1", "metric_key": "x", "threshold": 0.5}],
        }
        errors = pm.validate(policy)
        assert any("operator" in e for e in errors)

    def test_validate_control_missing_threshold(self, pm):
        policy = {
            "title": "Partial",
            "controls": [{"id": "C1", "metric_key": "x", "operator": ">"}],
        }
        errors = pm.validate(policy)
        assert any("threshold" in e for e in errors)

    def test_validate_control_missing_multiple_fields(self, pm):
        """A control missing all required fields produces 4 errors."""
        policy = {
            "title": "Empty control",
            "controls": [{}],
        }
        errors = pm.validate(policy)
        assert len(errors) == 4  # id, metric_key, operator, threshold

    def test_validate_multiple_controls_mixed(self, pm):
        """Reports errors from the correct control index."""
        policy = {
            "title": "Mixed",
            "controls": [
                {"id": "C1", "metric_key": "x", "operator": ">", "threshold": 0.5},
                {"id": "C2"},  # missing 3 fields
            ],
        }
        errors = pm.validate(policy)
        assert len(errors) == 3
        assert all("Control 1" in e for e in errors)

    def test_validate_control_id_unknown_fallback(self, pm):
        """When 'id' is missing, error message says 'unknown'."""
        policy = {
            "title": "No id",
            "controls": [{"metric_key": "x", "operator": ">", "threshold": 0.5}],
        }
        errors = pm.validate(policy)
        assert any("unknown" in e for e in errors)

    def test_validate_both_title_and_controls_missing(self, pm):
        errors = pm.validate({})
        assert len(errors) == 2


# ===========================================================================
# get_schema()
# ===========================================================================


class TestGetSchema:
    def test_returns_policy_schema(self):
        schema = PolicyManager.get_schema()
        assert schema is POLICY_SCHEMA
        assert schema["title"] == "Venturalitica Simplified OSCAL Policy"
        assert "controls" in schema["properties"]
        assert "title" in schema["required"]

    def test_schema_structure(self):
        schema = PolicyManager.get_schema()
        ctrl_props = schema["properties"]["controls"]["items"]["properties"]
        assert "id" in ctrl_props
        assert "metric_key" in ctrl_props
        assert "operator" in ctrl_props
        assert "threshold" in ctrl_props
        assert "severity" in ctrl_props


# ===========================================================================
# __init__ paths
# ===========================================================================


class TestInit:
    def test_target_dir_is_path(self, tmp_path):
        pm = PolicyManager(str(tmp_path))
        assert pm.target_dir == tmp_path
        assert pm.policy_path == tmp_path / "model_policy.oscal.yaml"
