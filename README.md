# Dataset 
This folder contains the reference images for the dataset generation.

# Instructions
## Python code
The required packages are listed in the `requirements.txt` file.

```shell
pip install -r requirements.txt
```

## Dataset generation
The reference images for both enrollment and authentication phases are the provided in the dataset folder (__dataset/reference_images__).
Start the python shell and run the following command line:

```python
from nofakes import dataset_generation

dataset_generation()
```

## main.py
Variables and functions are defined for running both enrollment and authentication phases. The code can be run in parallel by changing the number of cores (`N_CORES`).
Run the following command from the root directory on your local machine.

```shell
python main.py
```