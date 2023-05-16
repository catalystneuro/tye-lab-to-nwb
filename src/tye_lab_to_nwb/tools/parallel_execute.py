import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional, List

from nwbinspector.utils import calculate_number_of_cpu
from tqdm import tqdm


def parallel_execute(session_to_nwb_function, kwargs_list: List[dict], num_parallel_jobs: Optional[int] = 1):
    """
    Wraps a function for parallel execution using multiple processes.

    Parameters
    ----------
    session_to_nwb_function : callable
        The function to be executed in parallel.
    kwargs_list : list
        A list of keyword arguments to be passed to the function.
    num_parallel_jobs: int, optional
        The number of parallel jobs. The default is to use one process at a time.
        When not specified (num_parallel_jobs=None) it is set to use all available CPUs.
    """
    if num_parallel_jobs is None:
        num_parallel_jobs = os.cpu_count()

    max_workers = calculate_number_of_cpu(requested_cpu=num_parallel_jobs)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []

        for kwargs in kwargs_list:
            futures.append(executor.submit(session_to_nwb_function, **kwargs))

        with tqdm(total=len(futures), position=0, leave=True) as progress_bar:
            for future in as_completed(futures):
                future.result()
                progress_bar.update(1)
