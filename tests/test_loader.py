import os
import tempfile

import pytest
import yaml

from venturalitica.loader import OSCALPolicyLoader


def test_loader_file_not_found():
    with pytest.raises(FileNotFoundError):
        OSCALPolicyLoader("non_existent.yaml").load()


def test_loader_invalid_format():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"unknown": "root"}, f)
        path = f.name
    try:
        with pytest.raises(ValueError, match="Unsupported OSCAL format"):
            OSCALPolicyLoader(path).load()
    finally:
        os.unlink(path)


def test_loader_flat_list():
    data = [
        {"id": "C1", "metric_key": "accuracy_score", "threshold": 0.8, "operator": ">="}
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        path = f.name
    try:
        policy = OSCALPolicyLoader(path).load()
        assert policy.title == "Flat Policy"
        assert len(policy.controls) == 1
        assert policy.controls[0].metric_key == "accuracy_score"
    finally:
        os.unlink(path)


def test_loader_catalog_recursive():
    data = {
        "catalog": {
            "metadata": {"title": "Recursive Catalog"},
            "controls": [
                {
                    "id": "G1",
                    "title": "Group 1",
                    "controls": [
                        {
                            "id": "C1",
                            "title": "Nested Control",
                            "props": [
                                {"name": "metric_key", "value": "f1_score"},
                                {"name": "threshold", "value": "0.7"},
                                {"name": "operator", "value": ">="},
                                {"name": "severity", "value": "high"},
                            ],
                        }
                    ],
                }
            ],
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        path = f.name
    try:
        policy = OSCALPolicyLoader(path).load()
        assert len(policy.controls) == 1
        assert policy.controls[0].id == "C1"
        assert policy.controls[0].severity == "high"
    finally:
        os.unlink(path)


def test_loader_direct_props():
    data = {
        "assessment-plan": {
            "control-implementations": [
                {
                    "implemented-requirements": [
                        {
                            "control-id": "C1",
                            "props": [
                                {"name": "metric_key", "value": "precision_score"},
                                {"name": "threshold", "value": "0.9"},
                                {"name": "operator", "value": ">="},
                                {"name": "input:target", "value": "y_true"},
                            ],
                        }
                    ]
                }
            ]
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        path = f.name
    try:
        policy = OSCALPolicyLoader(path).load()
        assert len(policy.controls) == 1
        assert policy.controls[0].metric_key == "precision_score"
        assert policy.controls[0].input_mapping["target"] == "y_true"
        assert policy.controls[0].input_mapping["target"] == "y_true"
    finally:
        os.unlink(path)


def test_loader_hybrid_inventory():
    data = {
        "assessment-plan": {
            "inventory-items": [  # Directly at root of AP
                {
                    "uuid": "m1",
                    "props": [{"name": "metric_key", "value": "recall_score"}],
                }
            ],
            "control-implementations": [
                {
                    "implemented-requirements": [
                        {"control-id": "C1", "links": [{"href": "#m1"}]}
                    ]
                }
            ],
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        path = f.name
    try:
        policy = OSCALPolicyLoader(path).load()
        assert len(policy.controls) == 1
        assert policy.controls[0].metric_key == "recall_score"
    finally:
        os.unlink(path)


def test_oscal_loader_from_dict():
    """Test OSCALPolicyLoader loading from a dictionary with SSP format."""
    policy_data = {
        "system-security-plan": {
            "metadata": {"title": "Test Policy"},
            "control-implementation": {
                "implemented-requirements": [
                    {
                        "control-id": "ctrl1",
                        "description": "Test control",
                        "props": [
                            {"name": "metric_key", "value": "accuracy"},
                            {"name": "operator", "value": ">="},
                            {"name": "threshold", "value": "0.9"},
                        ],
                    }
                ]
            },
        }
    }

    loader = OSCALPolicyLoader(policy_data)
    policy = loader.load()
    assert policy is not None
    assert len(policy.controls) > 0
