# Expression Generate Process

## generate_expression_single:

Generate expressions with a single operator.

### How to Use

To run the script, execute the following command with the desired parameters:

```bash
python generate_expression_single.py \
    --config <config_path> \
    --cython-cache-dir <cython_cache_dir> \
    --operators-path <operators_path> \
    --generated-expression-path <generated_expression_path> \
    --num <num> \
    --workers <workers> \
    --func_id <func_id> \
    --base <base>
```
#### Command-Line Arguments:

- `--config`: The path to the configuration file for the expression generation process.
- `--cython-cache-dir`: The directory where the Cython cache is stored.
- `--operators-path`: The path to the JSONL file containing the operators to be used in the generation (e.g., `final_base.jsonl`).
- `--generated-expression-path`: The directory where the generated expressions will be saved (e.g., `data/exps/expr_test`).
- `--num`: The number of expressions to generate (default: 10000).
- `--workers`: The number of worker processes to use for parallelism (default: 8).
- `--func_id`: The function ID for expression generation. Use `"all"` to generate expressions for all operators.
- `--base`: The numerical base for expression generation (e.g., 10 for decimal, 2 for binary).

#### Bash Script for Convenience
To facilitate the execution process, a bash script is provided that can be run with modified parameters.

```bash
nohup bash run_generate_singleop_expression.sh > output.log 2>&1 &
```

## generate_expression_combination:

Generate expressions containing combinations of operators for different bases at different depths.

### How to Use

To run the script, execute the following command with the desired parameters:

```bash
python generate_expression_combination.py \
    --config <config_path> \
    --cython-cache-dir <cython_cache_dir> \
    --operators-path <operators_path> \
    --generated-expression-path <generated_expression_path> \
    --generated-opexpr-dependency-path <generated_opexpr_dependency_path> \
    --num <num> \
    --workers <workers> \
    --base <base> \
    --depth <depth>
```

#### Command-Line Arguments:

- `--config`: The path to the configuration file for the expression generation process.
- `--cython-cache-dir`: The directory where the Cython cache is stored.
- `--operators-path`: The path to the JSONL file containing the operators to be used in the generation.
- `--generated-expression-path`: The directory where the generated expressions will be saved.
- `--generated-opexpr-dependency-path`: The path to save dependencies related to the generated expressions.
- `--num`: The number of expressions to generate.
- `--workers`: The number of worker processes to use for parallelism.
- `--base`: The numerical base for expression generation.
- `--depth`: The depth of the expressions to generate (default: 2). Higher depth means more complex expressions.


#### Bash Script for Convenience
To facilitate the execution process, a bash script is provided that can be run with modified parameters.

```bash
nohup run_generate_expression_base_n_depth_m.sh > output.log 2>&1 &
```