from venturalitica.artifacts import FileArtifact


def test_file_artifact_missing():
    art = FileArtifact("non_existent_file.txt")
    assert art.get_fingerprint() == "MISSING"
    d = art.to_dict()
    assert d["fingerprint"] == "MISSING"
    assert "non_existent_file.txt" in d["path"]

def test_file_artifact_real(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    art = FileArtifact(str(f))
    fp = art.get_fingerprint()
    assert fp != "MISSING"
    assert len(fp) == 64 # sha256
