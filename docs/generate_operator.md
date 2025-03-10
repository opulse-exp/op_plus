# Operator Generate Process

## generate_operator_type

Generate an operator of a certain order and a certain type of definition.

### How to Use

To run the script, execute the following command with the desired parameters:

```bash
python generate_operator_type.py \
    --config <config_path> \
    --initial-operators-path <initial_operators_path> \
    --generated-operators-path <generated_operators_path> \
    --cython-cache-dir <cython_cache_dir> \
    --mode <mode> \
    --num <num> \
    --n_order <n_order>
```
Command-Line Arguments:

- `--config`: The path to the configuration YAML file for operator generation.
- `--initial-operators-path`: The path to the initial operator JSONL file.
- `--generated-operators-path`: The path where the generated operators will be saved.
- `--cython-cache-dir`: The directory where Cython compiled functions will be cached.
- `--mode`: The mode for operator generation. Choose between:
  - `raise`: Generate operators for the **raise** mode (e.g., exponentiation-like operations, which represent higher-order relationships).
  - `expand`: Generate operators for the **expand** mode (e.g., expansion operations like polynomial expansion or algebraic transformations).
- `--num`: The number of operators to generate.
- `--n_order`: The order of the operators to generate.


## generate_operator_multiprocess

Generate operators at a large scale using multiprocessing.

### How to Use

To run the script, execute the following command with the desired parameters:

```bash
python generate_operator_multiprocess.py \
    --config <config_path> \
    --initial-operators-path <initial_operators_path> \
    --generated-operators-path <generated_operators_path> \
    --cython-cache-dir <cython_cache_dir> \
    --num <num> \
    --max-workers <max_workers> \
    --ratio <ratio> \
    --raise-increase-at-order <raise_increase_at_order> \
    --increase-count <increase_count> \
    --continue-mode <continue_mode>

```
Command-Line Arguments:

- `--config`: The path to the configuration YAML file for operator generation.
- `--initial-operators-path`: The path to the initial operator JSONL file.
- `--generated-operators-path`: The path where the generated operators will be saved.
- `--cython-cache-dir`: The directory where Cython compiled functions will be cached.
- `--num`: The number of operators to generate.
- `--max-workers`: This argument specifies the maximum number of worker processes for parallel execution. 
- `--ratio`: This argument specifies the ratio of each layer compared to the previous one, which is useful for expanding operators. The default value is `0.6`.
- `--raise-increase-at-order`: At which order the recursive definition starts generating higher-order operators.. The default value is `3`.
- `--increase-count`: This argument specifies the number of operators to add after the raise-order point is reached. The default value is `3`.
- `--continue-mode`: This argument specifies whether to continue the generation process from the last checkpoint (`True`) or start a fresh generation process (`False`). The default value is `True`.

Bash Script for Convenience；

To facilitate the execution process, a bash script is provided that can be run with modified parameters.

```bash
nohup bash run_generate_operator_multiprocess.sh > output.log 2>&1 &
```

## assign_operator_priority

Assign priority and associativity after the operator data generation completes.

### How to Use  

To run the script, execute the following command with the desired parameters:

```bash
python assign_operator_priority.py \
    --config <config_path> \
    --operator-file <operator_input_path> \
    --output-operator-file <output_operator_path> \
    --cython-cache-dir <cython_cache_directory>
```

Command-Line Arguments:

- `--config`: The path to the configuration YAML file for operator generation.
- `--operator-file`: Defines the path to the input JSONL file containing the initial operator data. This argument is required.  
- `--output-operator-file`: Determines the output path where the generated operators will be stored. This is also a required argument.  
- `--cython-cache-dir`: Specifies the directory where Cython compiled functions will be cached. 

## generate_base_operator

Generate unary operators representing various bases.

### How to Use  

To run the script, execute the following command with the desired parameters: 

```bash
python generate_base_operator.py \
    --config <config_path> \
    --max_base <max_base_value> \
    --operator-file <operator_file_path> \
    --output-file <output_file_path> \
    --cython-cache-dir <cython_cache_directory>
```

Command-Line Arguments:

- `--config`: Specifies the path to the configuration file that defines the operator generation rules.
- `--max_base`:Defines the maximum base value for numeral systems in the generated operators.
- `--operator-file`: Indicates the path to the input file containing existing operators. 
- `--output-file`: Specifies the path where the generated operators will be saved. 
- `--cython-cache-dir`: Defines the directory where Cython compiled functions will be stored.   

## op_func_transform
Reverse transform a computation function back into an operator definition.