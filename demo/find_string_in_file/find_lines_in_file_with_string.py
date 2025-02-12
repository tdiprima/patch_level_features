"""
This script extracts lines containing a specific substring from a source text file and writes those lines to a
destination text file, while also providing utility functions for searching and modifying strings within files.
https://www.quora.com/How-do-I-write-a-python-script-that-will-find-a-specific-string-in-a-txt-file-select-the-rest-of-string-surrounding-it-and-paste-in-another-txt
"""


def get_lines_with(input_str, substr):
    """
    Get all lines containing a substring.

    Args:
        input_str (str): String to get lines from.
        substr (str): Substring to look for in lines.

    Returns:
        list[str]: List of lines containing substr.
    """
    lines = []
    for line in input_str.strip().split('\n'):
        if substr in line:
            lines.append(line)
    return lines


def remove_substr(big_str, substr):
    """
    If you want to remove the string you're looking for,
    use this on each line you get, in the get_lines_with function.
    :param big_str:
    :param substr:
    :return:
    """
    if substr not in big_str:
        return big_str
    start_index = big_str.index(substr)
    end_index = start_index + len(substr)
    return big_str[:start_index] + big_str[end_index:]


def txt_lines_with(fname, substr):
    """
    Get all lines in a .txt file containing a substring.

    Args:
        fname (str): File name to open.
        substr (str): Substring to look for in lines.

    Returns:
        list[str]: List of lines containing substr.
    """
    f_contents = open(fname, 'r').read()
    return get_lines_with(f_contents, substr)


def filter_txt_lines_to(fname_in, substr, fname_out):
    """
    Put lines from one .txt file into another if they
    contain a substring 'substr'.

    Args:
        fname_in (str): Source file.
        substr (str): Substring to look for in lines.
        fname_out (str): Destination file.
    """
    filtered_lines = txt_lines_with(fname_in, substr)
    joined_lines = '\n'.join(filtered_lines)
    open(fname_out, 'w').write(joined_lines)


# Add your file names and filter here
filter_txt_lines_to("./source.txt", "nulla", "./dest.txt")
