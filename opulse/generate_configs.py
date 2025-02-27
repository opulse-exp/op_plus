import yaml
import os

# 定义要生成的配置列表
bases = range(2,17)
depths = [2, 4, 6, 8, 10]

# 加载模板文件
with open('config/exp_configs/generate_expression_depth2.yaml', 'r') as file:
    template = yaml.safe_load(file)

# 生成并保存每个配置的 YAML 文件
for base in bases:
    for depth in depths:
        if base == 10:
            continue
        # 修改模板中的 base 和 expr_max_depth 字段
        template['random_base']['base'] = base
        template['result_base']['base'] = base
        template['longer_result_compute']['base'] = base
        template['expr_max_depth'] = depth
        
        # 构造输出文件名
        output_filename = f"config/exp_configs/generate_expression_base{base}_depth{depth}.yaml"
        
        # 保存生成的 YAML 文件
        with open(output_filename, 'w') as output_file:
            yaml.dump(template, output_file, default_flow_style=False)
        
        print(f"已生成文件: {output_filename}")