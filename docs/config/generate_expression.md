# YAML Configuration for Expression Generation

## 1. **Logging Configuration**

```yaml
logging:
  level: INFO  # INFO or DEBUG, WARNING, ERROR, CRITICAL
  log_dir: "logs"  # Log directory
  log_file: "data.log"  # Log file name
  save_file: true  # Whether to save the logs to a file
```
- **level**: Defines the logging level. Options include `DEBUG`, `WARNING`, `ERROR`, and `CRITICAL`. It controls the verbosity of the logs. `DEBUG` is the most detailed.
- **log_dir**: The directory where log files will be stored.
- **log_file**: The name of the log file that will contain the logs.
Sure! Here's the full explanation for the logging section, continuing from where you left off:
- **save_file**: A flag to specify whether to save the logs to a file. If set to `true`, the logs will be written to the log file. If set to `false`, logging information may be displayed on the console or ignored, depending on other configurations.
---

## 2. **Numeric Representation**

```yaml
max_base: 16
custom_digits: "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
```
- **max_base**: The maximum numeric base to be used for numerical operations. In this case, the base is set to 16, allowing hexadecimal operations.
- **custom_digits**: A string defining the custom set of digits used for representing numbers in different bases. Here it supports bases up to 36, with digits 0-9 and letters A-Z.

---

## 3. **Other Symbol Atoms**

```yaml
other_symbols_atoms:
  left_parenthesis: "(" 
  right_parenthesis: ")"
  equals_sign: "="
  nan_symbol: "NaN" 
  inf_symbol: "Inf"  
  neg_inf_symbol: "-Inf"  
```
- **left_parenthesis**: Defines the left parenthesis `(` used in expressions.
- **right_parenthesis**: Defines the right parenthesis `)` used in expressions.
- **equals_sign**: Defines the equal sign `=`, typically used for assignments or equality checks.
- **nan_symbol**: Defines the symbol for "NaN" (Not a Number), indicating that the expression does not have a solution.
- **inf_symbol**: Defines the symbol for positive infinity.
- **neg_inf_symbol**: Defines the symbol for negative infinity.

---

## 4. **Expression Generation**

```yaml
expr_variables:
  - a
  - b
expr_numeric_range: 
  max_value: 1000
  min_value: 0 
expr_max_depth: 3
expr_type_weights: 
  binary: 0.7
  unary_prefix: 0.2
  unary_postfix: 0.1
  atoms: 0 # Indicates that only numbers, not single variables, will be generated as atoms
expr_atom_type_weights: 
  variable: 0.3
  number: 0.7
random_base:
  flag: false
  base: 10
result_base: 
  random_flag: false
  base: 10
longer_result_compute:
  flag: true
  base: 10
```

- **expr_variables**: Defines the variables available for expression generation. In this case, only `a` and `b` will be used as operands.

- **expr_numeric_range**: Specifies the numeric range for the expressions, from `0` to `1000`. This applies to numeric atoms and intermediate values.

- **expr_max_depth**: Sets the maximum depth of generated expressions. A depth of `3` allows up to three levels of nested operations.

- **expr_type_weights**: Specifies the probability distribution for expression types:
  - **binary (0.7)**: 70% binary operations (e.g., `a + b`).
  - **unary_prefix (0.2)**: 20% unary prefix operations (e.g., `-a`).
  - **unary_postfix (0.1)**: 10% unary postfix operations (e.g., `a!`).
  - **atoms (0)**: No single variables or numbers generated as atoms.

- **expr_atom_type_weights**: Defines the probability of atoms being variables or numbers:
  - **variable (0.3)**: 30% variables (e.g., `a`, `b`).
  - **number (0.7)**: 70% numbers (e.g., `1`, `42`, `1000`).

- **random_base**: Determines if random bases will be used for numbers. If enabled (`true`), numbers can be in different bases. Default is decimal (`base: 10`).

- **result_base**: Controls the base for the result of expressions. Default is decimal (`base: 10`), but it can be randomly selected if enabled.

- **longer_result_compute**: Enables more complex calculations for longer results. If enabled (`true`), results will be computed in the specified base (`base: 10`).


