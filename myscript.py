case_id = ''
username = ''


def get_file_list(substr):
    lines = []
    with open('config/csv_file_path.list') as f:
        for line in f:
            if substr in line:
                lines.append(line)
    f.close()
    return lines

