conda create --name op_plus python=3.10

cd op_plus/opulse

pip install -r requirement.txt

##生成单个运算符的表达式(各种进制)

bash run_generate_singleop_expression.sh

##生成运算符组合的表达式(各种深度各种进制)

bash run_generate_expression_base_n_depth_m.sh
