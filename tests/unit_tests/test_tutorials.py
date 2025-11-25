import pytest
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError


@pytest.fixture
def tutorials_dir():
    """Path to tutorials directory"""
    return Path(__file__).parent.parent.parent / "tutorials_how_to"


def execute_notebook(notebook_path, timeout=300):
    """
    Execute a Jupyter notebook and return detailed results.
    
    Returns:
        tuple: (success: bool, error_message: str)
    """
    try:
        with open(notebook_path) as f:
            nb = nbformat.read(f, as_version=4)
        
        # Create client with working directory set to notebook's directory
        client = NotebookClient(
            nb,
            timeout=timeout,
            kernel_name='python3',
            resources={'metadata': {'path': str(notebook_path.parent)}}
        )
        
        # Execute the notebook
        client.execute()
        
        return True, ""
            
    except CellExecutionError as e:
        # This exception contains detailed cell execution info
        error_msg = f"Error in cell {e.cellnum}:\n"
        error_msg += f"{e.traceback}\n"
        return False, error_msg
        
    except TimeoutError as e:
        return False, f"Notebook execution timed out after {timeout} seconds"
        
    except Exception as e:
        return False, f"Unexpected error: {type(e).__name__}: {str(e)}"


def collect_notebooks(tutorials_dir):
    """Collect all notebook files from the tutorials directory, sorted alphabetically"""
    notebooks = list(tutorials_dir.glob("*.ipynb"))
    # Exclude Jupyter checkpoint files
    notebooks = [nb for nb in notebooks if ".ipynb_checkpoints" not in str(nb)]
    # Sort alphabetically
    return sorted(notebooks, key=lambda p: p.name)


@pytest.mark.tutorials
def test_all_tutorial_notebooks_run_sequentially(tutorials_dir):
    """Test that all tutorial notebooks execute without errors in alphabetical order"""
    
    notebooks = collect_notebooks(tutorials_dir)
    
    if not notebooks:
        pytest.skip("No notebooks found in tutorials directory")
    
    failed_notebooks = []
    
    for notebook_path in notebooks:
        print(f"\n{'='*70}")
        print(f"Running: {notebook_path.name}")
        print(f"{'='*70}")
        
        success, error_output = execute_notebook(notebook_path, timeout=600)
        
        if not success:
            failed_notebooks.append({
                'name': notebook_path.name,
                'path': notebook_path,
                'error': error_output
            })
            # Continue running remaining notebooks to see all failures
            print(f"❌ FAILED: {notebook_path.name}")
        else:
            print(f"✅ PASSED: {notebook_path.name}")
    
    # Report all failures at the end
    if failed_notebooks:
        error_msg = f"\n{'='*70}\n"
        error_msg += f"{len(failed_notebooks)} notebook(s) failed to execute:\n"
        error_msg += f"{'='*70}\n"
        
        for idx, failed in enumerate(failed_notebooks, 1):
            error_msg += f"\n{idx}. {failed['name']}\n"
            error_msg += f"{'-'*70}\n"
            error_msg += f"Location: {failed['path']}\n"
            error_msg += f"Executed from: {failed['path'].parent}\n"
            if failed['error']:
                error_msg += f"\nError:\n{failed['error']}\n"
            error_msg += f"\nTo debug interactively:\n"
            error_msg += f"  jupyter notebook {failed['path']}\n"
        
        pytest.fail(error_msg)
    
    print(f"\n{'='*70}")
    print(f"✅ All {len(notebooks)} notebooks executed successfully!")
    print(f"{'='*70}")