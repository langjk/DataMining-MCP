# test_tool_call.py
# 测试工具调用功能

import json
from gpt_dispatcher import dispatch_gpt_response

def test_data_analysis_call():
    """测试数据分析工具调用"""
    print("=" * 50)
    print("测试数据分析工具调用")
    print("=" * 50)
    
    # 模拟GPT返回的JSON（修正后的格式）
    gpt_response = {
        "action": "invoke_tool",
        "tool": "data_analysis",
        "args": {
            "analysis_type": "comprehensive",
            "file_path": "./data/测试数据正（公开）/振动（公开）/XXX-254-31Z01-01随机振动试验（公开）.csv"
        },
        "description": "用户要求对第1批次振动数据进行全面分析"
    }
    
    # 转换为JSON字符串
    gpt_reply_text = json.dumps(gpt_response, ensure_ascii=False)
    print(f"模拟GPT回复:\n{gpt_reply_text}")
    
    # 调用工具调度器
    try:
        result = dispatch_gpt_response(gpt_reply_text)
        print(f"\n工具调用结果类型: {result['type']}")
        
        if result["type"] == "tool_result":
            print("✅ 工具调用成功!")
            data = result["data"]
            print(f"分析类型: {data['analysis_type']}")
            print(f"文件路径: {data['file_path']}")
            print(f"文件元数据: {data['file_metadata']}")
            
            # 显示分析结果摘要
            analysis = data["analysis_results"]
            print(f"\n数据质量: {analysis['data_quality']['quality_rating']}")
            print(f"分析的列数: {analysis['summary']['analyzed_columns']}")
            print(f"总记录数: {analysis['summary']['total_records']}")
            
        elif result["type"] == "error":
            print(f"❌ 工具调用失败: {result['content']}")
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")

def test_batch_comparison_call():
    """测试批次对比工具调用"""
    print("\n" + "=" * 50)
    print("测试批次对比工具调用")
    print("=" * 50)
    
    # 模拟批次对比调用
    gpt_response = {
        "action": "invoke_tool",
        "tool": "batch_comparison",
        "args": {
            "batch1_path": "./data/测试数据正（公开）/振动（公开）/XXX-254-31Z01-02随机振动试验（公开）.csv",
            "batch2_path": "./data/测试数据正（公开）/振动（公开）/XXX-254-31Z01-05随机振动试验（公开）.csv",
            "batch1_name": "第2批次",
            "batch2_name": "第5批次"
        },
        "description": "用户要求对比第2批次和第5批次的稳定性"
    }
    
    gpt_reply_text = json.dumps(gpt_response, ensure_ascii=False)
    print(f"模拟GPT回复:\n{gpt_reply_text}")
    
    try:
        result = dispatch_gpt_response(gpt_reply_text)
        print(f"\n工具调用结果类型: {result['type']}")
        
        if result["type"] == "tool_result":
            print("✅ 批次对比调用成功!")
            data = result["data"]
            comparison = data["comparison_results"]
            print(f"对比: {comparison['batch1_name']} vs {comparison['batch2_name']}")
            print(f"对比指标数量: {len(comparison['comparison'])}")
            
            # 显示前3个指标的对比结果
            count = 0
            for metric, comp_data in comparison['comparison'].items():
                if count >= 3:
                    break
                print(f"- {metric}: 改进评估={comp_data['improvement']}, 稳定性={comp_data['stability_comparison']}")
                count += 1
                
        elif result["type"] == "error":
            print(f"❌ 批次对比调用失败: {result['content']}")
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")

if __name__ == "__main__":
    # 测试数据分析调用
    test_data_analysis_call()
    
    # 测试批次对比调用
    test_batch_comparison_call()
    
    print("\n" + "=" * 50)
    print("工具调用测试完成!")
    print("=" * 50)