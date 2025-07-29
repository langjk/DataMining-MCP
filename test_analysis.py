# test_analysis.py
# 测试改进后的数据分析功能

from data_analyzer import DataAnalyzer
from csv_reader import read_csv_clean
import json

def test_batch3_analysis():
    """测试第3批次数据分析"""
    print("=" * 50)
    print("测试第3批次数据分析")
    print("=" * 50)
    
    # 文件路径
    file_path = "./data/测试数据正（公开）/振动（公开）/XXX-254-31Z01-03随机振动试验（公开）.csv"
    
    try:
        # 读取数据
        df, meta = read_csv_clean(file_path)
        print(f"文件元数据: {meta}")
        print(f"数据形状: {df.shape}")
        print(f"列名: {list(df.columns)}")
        
        # 创建分析器
        analyzer = DataAnalyzer()
        
        # 执行全面分析
        result = analyzer.comprehensive_analysis(df, time_col="时间")
        
        # 打印结果摘要
        print("\n数据质量评估:")
        quality = result["data_quality"]
        print(f"- 质量评级: {quality['quality_rating']}")
        print(f"- 平均完整性: {quality['average_completeness']:.2f}%")
        print(f"- 分析列数: {len(quality['completeness_rates'])}")
        
        print("\n关键发现:")
        summary = result["summary"]
        for finding in summary["key_findings"][:3]:  # 只显示前3个
            print(f"- {finding['column']}: {', '.join(finding['findings'])}")
        
        print("\n基础统计分析（前5个指标）:")
        stats = result["basic_statistics"]
        count = 0
        for col, data in stats.items():
            if count >= 5:
                break
            print(f"- {col}: 均值={data['mean']:.4f}, 标准差={data['std']:.4f}, 变异系数={data['cv']:.4f}")
            count += 1
        
        print("\n稳定性分析（前5个指标）:")
        stability = result["stability_analysis"]
        count = 0
        for col, data in stability.items():
            if count >= 5:
                break
            print(f"- {col}: 稳定性评级={data['stability_rating']}, 稳定性指数={data['stability_index']:.4f}")
            count += 1
        
        return result
        
    except Exception as e:
        print(f"分析失败: {str(e)}")
        return None

def test_batch_comparison():
    """测试批次对比分析"""
    print("\n" + "=" * 50)
    print("测试第2批次与第5批次对比分析")
    print("=" * 50)
    
    file1 = "./data/测试数据正（公开）/振动（公开）/XXX-254-31Z01-02随机振动试验（公开）.csv"
    file2 = "./data/测试数据正（公开）/振动（公开）/XXX-254-31Z01-05随机振动试验（公开）.csv"
    
    try:
        # 读取数据
        df1, meta1 = read_csv_clean(file1)
        df2, meta2 = read_csv_clean(file2)
        
        print(f"第2批次数据: {df1.shape}")
        print(f"第5批次数据: {df2.shape}")
        
        # 创建分析器
        analyzer = DataAnalyzer()
        
        # 执行批次对比
        result = analyzer.batch_comparison(df1, df2, batch1_name="第2批次", batch2_name="第5批次")
        
        print(f"\n对比结果 ({result['batch1_name']} vs {result['batch2_name']}):")
        comparison = result["comparison"]
        
        count = 0
        for col, data in comparison.items():
            if count >= 5:  # 只显示前5个指标
                break
            print(f"\n- {col}:")
            print(f"  均值变化: {data['mean_change_percent']:.2f}%")
            print(f"  稳定性对比: {data['stability_comparison']}")
            print(f"  改进评估: {data['improvement']}")
            print(f"  统计显著性: {'是' if data['significant_difference'] else '否'}")
            count += 1
        
        return result
        
    except Exception as e:
        print(f"对比分析失败: {str(e)}")
        return None

if __name__ == "__main__":
    # 测试第3批次全面分析
    result1 = test_batch3_analysis()
    
    # 测试批次对比分析
    result2 = test_batch_comparison()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)