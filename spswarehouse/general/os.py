import os
from glob import glob

def make_directory_if_does_not_exist(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f'Directory "{path}" created.')
    else:
        print(f'Directory "{path}" already exists.')

def get_most_recent_file_in_dir(folder_path):
    """Returns the most recently changed file in a folder.

    Args:
        folder_path: The path to the folder to search
    Returns:
        A string with the filename of the most recently changed file in the
        folder.
    """
    # * means all if need specific format then *.csv
    list_of_files = glob(folder_path + '/*')
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file