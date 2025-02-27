#!/bin/bash

# 执行 clean 和 build_ext 命令
python operatorplus/setup.py clean --all

# 执行 build_ext 并检查结果
result=$(python operatorplus/setup.py build_ext --inplace)
if [ $? -eq 0 ]; then
    echo "Build completed successfully."
else
    echo "Build failed with status code $result."
fi
