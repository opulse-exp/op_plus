# YAML Configuration for Operator Generation

## 1. Logging Configuration

```yaml
logging:
  level: INFO  # INFO or DEBUG, WARNING, ERROR, CRITICAL
  log_dir: "logs"  # Log directory
  log_file: "data.log"  # Log file name
  save_file: true  # Whether to save the logs to a file
```
- `level`: Defines the logging level. Options include `DEBUG`, `WARNING`, `ERROR`, and `CRITICAL`. It controls the verbosity of the logs. `DEBUG` is the most detailed.
- `log_dir`: The directory where log files will be stored.
- `log_file`: The name of the log file that will contain the logs.
Sure! Here's the full explanation for the logging section, continuing from where you left off:
- `save_file`: A flag to specify whether to save the logs to a file. If set to `true`, the logs will be written to the log file. If set to `false`, logging information may be displayed on the console or ignored, depending on other configurations.
---

## 2. Numeric Representation

```yaml
max_base: 16
custom_digits: "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
```
- `max_base`: The maximum numeric base to be used for numerical operations. In this case, the base is set to 16, allowing hexadecimal operations.
- `custom_digits`: A string defining the custom set of digits used for representing numbers in different bases. Here it supports bases up to 36, with digits 0-9 and letters A-Z.

---

## 3. Variable Atoms

```yaml
variable_atoms:
  - left_operand: "a"
  - right_operand: "b"
```
- `variable_atoms`: Defines the variables that will be used as operands in expressions. Here, "a" is used as the left operand and "b" as the right operand.

---

## 4. Other Symbol Atoms

```yaml
other_symbols_atoms:
  left_parenthesis: "(" 
  right_parenthesis: ")"
  equals_sign: "="
  nan_symbol: "NaN" 
  inf_symbol: "Inf"  
  neg_inf_symbol: "-Inf"  
```
- `left_parenthesis`: Defines the left parenthesis `(` used in expressions.
- `right_parenthesis`: Defines the right parenthesis `)` used in expressions.
- `equals_sign`: Defines the equal sign `=`, typically used for assignments or equality checks.
- `nan_symbol`: Defines the symbol for "NaN" (Not a Number), indicating that the expression does not have a solution.
- `inf_symbol`: Defines the symbol for positive infinity.
- `neg_inf_symbol`: Defines the symbol for negative infinity.

---

## 5. Operator Generation

```yaml
operator_symbol_min_len: 1
operator_symbol_max_len: 3
basic_operator_symbols: ["+", "-", "*", "/", "%"]
comparison_ops: ["==", ">", "<", ">=", "<=", "!="]
logical_connectors: ["and", "or"]
condition_numeric_range:
  max_value: 1000
  min_value: 0
condition_probabilities:
  1: 0.7
  2: 0.2
  3: 0.1
```
- `operator_symbol_min_len`: Minimum length of an operator symbol. For example, the `+` symbol has a length of 1.
- `operator_symbol_max_len`: Maximum length of an operator symbol. This will limit operator lengths to 3 characters.
- `basic_operator_symbols`: A list of basic operators used for arithmetic calculations, such as addition (`+`), subtraction (`-`), multiplication (`*`), division (`/`), and modulus (`%`).
- `comparison_ops`: A list of comparison operators for conditions, such as equality (`==`), greater than (`>`), less than (`<`), etc.
- `logical_connectors`: A list of logical connectors used in expressions, such as `and` and `or`.
- `condition_numeric_range`: Defines the numeric range used for conditions. The values are between `0` and `1000` (no negative numbers here).
- `condition_probabilities`: Defines the probability distribution for different condition types. For example, there is a 70% chance that a condition will be of type 1, a 20% chance for type 2, and a 10% chance for type 3.

---

## 6. Configuration Parameters for Defining Strings Used in Expressions During Operator Definition Generation

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
  atoms: 0.1
expr_atom_type_weights: 
  variable: 0.8
  number: 0.2
```
- `expr_variables`: The variables used in expression generation.
- `expr_numeric_range`: Defines the numeric range used in expressions. The values range from 0 to 1000.
- `expr_max_depth`: The maximum depth of the generated expressions. For example, if set to 3, the expression will have a maximum of 3 levels of operations.
- `expr_type_weights`: Defines the probability distribution for the types of expressions to be generated. For example, 70% of expressions will be binary, 20% unary prefix, 10% unary postfix, and 10% atoms.
- `expr_atom_type_weights`: Defines the probability distribution for the types of atoms in the expressions. 80% will be variables and 20% will be numbers.

---

## 7. Base Configuration Settings Not Applied in Operator Generation

```yaml
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


