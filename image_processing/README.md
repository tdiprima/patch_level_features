# Image Processing and Workflow Automation Scripts

## Overview

This folder contains the following scripts:

1. **myscript.sh**
   - Automates the reading of a file containing a list of image-related tasks (`image_user_list.txt` or a provided file).
   - Extracts `case_id`, `user`, and `size` from the file and submits a batch job using `qsub` with the specified parameters.

2. **runscript.sh**
   - Executes a Python script (`myscript.py`) in a controlled environment after activating a Python virtual environment (`myenv`).
   - Prints execution metadata such as the date, host machine, and progress of the operation.

3. **myscript.pbs**
   - PBS script submitted as part of the job from `myscript.sh`.

4. **myscript.py**
   - A Python script invoked by `runscript.sh`. It processes slides or other data using specific parameters like user, database, and size.

---

## Prerequisites

- **Environment**: Ensure that the `myenv` or `feature-env` virtual environment exists and has all necessary dependencies installed.

   ```sh
   conda env create -f environment.yml
   conda activate feature-env
   ```
   
- **PBS Setup**: `myscript.sh` assumes a PBS job scheduler is configured and operational.
- **Input File**: Ensure that the input file (`image_user_list.txt` or custom) is available and formatted correctly with comma-separated values for `case_id`, `user`, and `size`.

---

## Usage Instructions

### Step 1: Prepare the Input File
The input file should contain lines with the following format:

```
case_id, user, size
```

Example:

```
1234, johndoe, 2048
5678, janedoe, 1024
```

### Step 2: Run the Scripts

#### To submit batch jobs:

```bash
bash myscript.sh [optional_input_file]

```

- If no input file is provided, it defaults to `image_user_list.txt`.

#### To run the Python script:

```bash
bash runscript.sh
```

- Ensure the `myenv` virtual environment is active and `myscript.py` is present.

---

## Notes
- Modify the parameters for `myscript.py` (`-s`, `-u`, `-b`, `-p`) in `runscript.sh` as needed for your use case.
- Ensure all dependencies are installed in the virtual environment (`myenv`).

---

## File Dependencies
- **myscript.sh** depends on:
  - `myscript.pbs`
  - An input file (default: `image_user_list.txt`)
- **runscript.sh** depends on:
  - `myscript.py`
  - `myenv` virtual environment

<br>
