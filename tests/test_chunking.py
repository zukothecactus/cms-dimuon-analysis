import pytest
from dimuon.analysis import run_chunked_analysis
from dimuon.demo import create_demo

@pytest.fixture
def demo_data(tmp_path):
    demo_file = tmp_path / "synthetic-demo.root"
    return create_demo(demo_file)

#equal number of events should be processed regardless of chunk size
def test_chunk_size_independance(demo_data, tmp_path):

    plot_path1 = tmp_path / "plot1.png"
    plot_path2 = tmp_path / "plot2.png"
    
    #run as a single batch, where chunk size is larger than the number of events
    cutflow_single_batch = run_chunked_analysis(
        file_path = demo_data,
        entry_start = 0,
        entry_stop = 5,
        chunk_size = 10,
        output_plot_path = plot_path1
    )
    
    #run as multiple batches, where chunk size is smaller than the number of events
    cutflow_multiple_batches = run_chunked_analysis(
        file_path = demo_data,
        entry_start = 0,
        entry_stop = 5,
        chunk_size = 2,
        output_plot_path = plot_path2
    )
    
    assert cutflow_single_batch["baseline"] == cutflow_multiple_batches["baseline"]
    assert cutflow_single_batch["pt_scan"] == cutflow_multiple_batches["pt_scan"]

def test_multiprocessing_invariance(demo_data, tmp_path):
    plot_path1 = tmp_path / "plot1.png"
    plot_path2 = tmp_path / "plot2.png"
    
    #run with a single worker (sequentially)
    cutflow_single_worker = run_chunked_analysis(
        file_path = demo_data,
        entry_start = 0,
        entry_stop = 5,
        chunk_size = 2,
        num_workers = 1,
        output_plot_path = plot_path1
    )
    
    #run with multiple workers (parallel)
    cutflow_multiple_workers = run_chunked_analysis(
        file_path = demo_data,
        entry_start = 0,
        entry_stop = 5,
        chunk_size = 2,
        num_workers = 2,
        output_plot_path = plot_path2
    )
    
    assert cutflow_single_worker["baseline"] == cutflow_multiple_workers["baseline"]
    assert cutflow_single_worker["pt_scan"] == cutflow_multiple_workers["pt_scan"]