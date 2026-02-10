import venturalitica as vl
import os
import json
import shutil

def test_monitor_label():
    """Verify that vl.monitor accepts a label and includes it in the trace artifact."""
    
    # Clean up previous traces
    trace_dir = ".venturalitica"
    if os.path.exists(trace_dir):
        shutil.rmtree(trace_dir)
    
    # Run monitor with label
    label_value = "Test Label"
    try:
        with vl.monitor(name="test-task", label=label_value):
            print("Running monitored task...")
            pass
    except TypeError as e:
        print(f"FAILED: vl.monitor raised TypeError: {e}")
        return

    # Verify trace file creation and content
    if not os.path.exists(trace_dir):
        print("FAILED: .venturalitica directory not created")
        return

    trace_files = [f for f in os.listdir(trace_dir) if f.startswith("trace_") and f.endswith(".json")]
    if not trace_files:
        print("FAILED: No trace file found")
        return

    trace_path = os.path.join(trace_dir, trace_files[0])
    with open(trace_path, 'r') as f:
        data = json.load(f)
    
    if data.get("label") == label_value:
        print("PASSED: Label found in trace metadata")
    else:
        print(f"FAILED: Label mismatch. Expected '{label_value}', got '{data.get('label')}'")

if __name__ == "__main__":
    test_monitor_label()
