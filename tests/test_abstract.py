import pytest
from venturalitica.probes import BaseProbe
from venturalitica.storage import BaseStorage

def test_abstract_probe():
    class DummyProbe(BaseProbe):
        def start(self): return super().start()
        def stop(self): return super().stop()
    
    p = DummyProbe("test")
    p.start()
    p.stop()
    assert p.get_summary() == ""

def test_abstract_storage():
    class DummyStorage(BaseStorage):
        def list_policies(self): pass
        def get_policy(self, name): pass
        def store_policy(self, path): pass
    
    s = DummyStorage()
    s.list_policies()
    s.get_policy("any")
    s.store_policy("any")

def test_base_storage_errors():
    s = BaseStorage()
    with pytest.raises(NotImplementedError):
        s.list_policies()
    with pytest.raises(NotImplementedError):
        s.get_policy("any")
