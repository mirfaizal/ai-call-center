import pytest
from unittest.mock import patch
from utils.generate_synthetic_transcripts import make_transcript, main

def test_make_transcript():
    res = make_transcript(1)
    assert res["call_id"] == "synthetic_0001"
    assert "agent" in res

@patch("argparse.ArgumentParser.parse_args")
def test_main(mock_args, tmp_path):
    # Mocking args
    mock_args.return_value.count = 2
    mock_args.return_value.outdir = str(tmp_path / "out")
    
    main()
    
    # Verify outputs
    outdir = tmp_path / "out"
    assert outdir.exists()
    files = list(outdir.glob("*"))
    assert len(files) == 2
