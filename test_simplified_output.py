# test_simplified_output.py
# 测试精简后的数据输出

import json
from gpt_dispatcher import dispatch_gpt_response

def test_comprehensive_analysis_simplified():
    """测试精简后的全面分析输出"""
    print("=" * 50)
    print("测试精简后的全面分析输出")
    print("=" * 50)
    
    gpt_response = {
        "action": "invoke_tool",
        "tool": "data_analysis",
        "args": {
            "analysis_type": "comprehensive",
            "file_path": "./data/测试数据正（公开）/振动（公开）/XXX-254-31Z01-01随机振动试验（公开）.csv"
        },
        "description": "测试精简输出"
    }
    
    gpt_reply_text = json.dumps(gpt_response, ensure_ascii=False)
    
    try:
        result = dispatch_gpt_response(gpt_reply_text)
        
        if result["type"] == "tool_result":
            data = result["data"]["analysis_results"]
            
            print("✅ 工具调用成功!")
            print(f"数据质量: {data['data_quality']['quality_rating']}")
            print(f"分析记录数: {data['summary']['total_records']}")
            
            print("\n📊 关键指标统计:")
            for metric, stats in data["key_metrics_statistics"].items():
                print(f"- {metric}: 均值={stats['mean']}, 变异系数={stats['cv']}")
            
            print("\n🎯 稳定性评估:")
            for metric, stability in data["key_metrics_stability"].items():
                print(f"- {metric}: {stability['stability_rating']} (指数={stability['stability_index']})")
            
            print("\n📈 趋势分析:")
            for metric, trend in data["key_metrics_trends"].items():
                print(f"- {metric}: {trend['trend_direction']}趋势 ({trend['trend_strength']}) 变化={trend['relative_change']}%")
            
            print("\n⚠️ 异常检测:")
            outlier_summary = data["outlier_summary"]
            print(f"- 总异常值: {outlier_summary['total_outliers']}")
            print(f"- 受影响指标: {outlier_summary['affected_metrics']}")
            
            # 计算JSON大小
            json_str = json.dumps(data, ensure_ascii=False)
            print(f"\n📊 数据大小: {len(json_str)} 字符")
            
            return True
            
        else:
            print(f"❌ 工具调用失败: {result.get('content', '')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_batch_comparison_simplified():
    """测试精简后的批次对比输出"""
    print("\n" + "=" * 50)
    print("测试精简后的批次对比输出")
    print("=" * 50)
    
    gpt_response = {
        "action": "invoke_tool",
        "tool": "batch_comparison",
        "args": {
            "batch1_path": "./data/测试数据正（公开）/振动（公开）/XXX-254-31Z01-01随机振动试验（公开）.csv",
            "batch2_path": "./data/测试数据正（公开）/振动（公开）/XXX-254-31Z01-02随机振动试验（公开）.csv",
            "batch1_name": "第1批次",
            "batch2_name": "第2批次"
        },
        "description": "测试批次对比精简输出"
    }
    
    gpt_reply_text = json.dumps(gpt_response, ensure_ascii=False)
    
    try:
        result = dispatch_gpt_response(gpt_reply_text)
        
        if result["type"] == "tool_result":
            data = result["data"]["comparison_results"]
            
            print("✅ 批次对比成功!")
            print(f"对比: {data['batch1_name']} vs {data['batch2_name']}")
            
            summary = data["comparison_summary"]
            print(f"\n📊 对比总结:")
            print(f"- 对比指标数: {summary['total_metrics']}")
            print(f"- 显著差异数: {summary['significant_differences']}")
            print(f"- 改进分布: {summary['improvement_distribution']}")
            
            print("\n🔍 关键差异:")
            for diff in data["key_differences"]:
                print(f"- {diff['metric']}: 变化{diff['mean_change_percent']}%, {diff['improvement']}, 稳定性{diff['stability_comparison']}")
            
            # 计算JSON大小
            json_str = json.dumps(data, ensure_ascii=False)
            print(f"\n📊 数据大小: {len(json_str)} 字符")
            
            return True
            
        else:
            print(f"❌ 批次对比失败: {result.get('content', '')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 测试精简后的全面分析
    success1 = test_comprehensive_analysis_simplified()
    
    # 测试精简后的批次对比
    success2 = test_batch_comparison_simplified()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ 所有精简输出测试通过！数据量已大幅减少，GPT可以正常处理。")
    else:
        print("❌ 精简输出测试存在问题")
    print("=" * 50)