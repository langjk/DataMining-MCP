# test_complete_workflow.py
# 测试完整的分析工作流程

import json
from gpt_dispatcher import dispatch_gpt_response

def simulate_gpt_analysis_response(tool_result_data):
    """模拟GPT接收工具结果后的分析响应"""
    
    # 从工具结果中提取关键信息
    analysis_results = tool_result_data.get("analysis_results", {})
    file_metadata = tool_result_data.get("file_metadata", {})
    analysis_type = tool_result_data.get("analysis_type", "")
    
    # 模拟GPT的分析总结
    key_findings = []
    overall_assessment = ""
    recommendations = []
    
    if analysis_type == "stability":
        # 稳定性分析总结
        stable_metrics = []
        for metric, data in analysis_results.items():
            rating = data.get("stability_rating", "")
            if rating == "极稳定":
                stable_metrics.append(metric)
        
        key_findings = [
            f"所有{len(analysis_results)}个关键指标均达到极稳定级别",
            f"Vi电压输入保持完全稳定(稳定性指数=1.0)",
            f"效率指标稳定性指数达到{analysis_results.get('效率', {}).get('stability_index', 0):.4f}"
        ]
        
        overall_assessment = f"第3批次设备在{file_metadata.get('rows', 0)}个测试点中表现出色的稳定性"
        
        recommendations = [
            "当前批次稳定性表现优秀，可以作为标准参考",
            "建议继续保持当前的生产工艺参数",
            "可以考虑适当提高测试负载以验证极限稳定性"
        ]
    
    elif analysis_type == "comprehensive":
        # 综合分析总结
        data_quality = analysis_results.get("data_quality", {})
        key_findings = [
            f"数据质量评级: {data_quality.get('quality_rating', '未知')}",
            f"完整性: {data_quality.get('average_completeness', 0):.1f}%",
            "所有关键电气参数均在正常范围内"
        ]
        
        overall_assessment = "设备运行状态良好，各项指标表现稳定"
        recommendations = ["继续监控关键参数变化", "定期进行稳定性评估"]
    
    # 构造标准的analysis_complete响应
    response = {
        "action": "analysis_complete",
        "analysis_summary": {
            "data_source": f"{file_metadata.get('filename', '未知文件')} ({file_metadata.get('rows', 0)}条记录)",
            "key_findings": key_findings,
            "overall_assessment": overall_assessment,
            "recommendations": recommendations
        }
    }
    
    return json.dumps(response, ensure_ascii=False)

def test_complete_workflow():
    """测试完整的工作流程：工具调用 -> 结果处理 -> GPT分析"""
    print("=" * 60)
    print("测试完整的分析工作流程")
    print("=" * 60)
    
    # 步骤1: 模拟用户请求 -> GPT工具调用
    print("🔹 步骤1: 用户请求 -> GPT工具调用")
    user_request = "分析第3批次的稳定性"
    print(f"用户请求: {user_request}")
    
    tool_call = {
        "action": "invoke_tool",
        "tool": "data_analysis",
        "args": {
            "analysis_type": "stability",
            "file_path": "./data/测试数据正（公开）/振动（公开）/XXX-254-31Z01-03随机振动试验（公开）.csv"
        },
        "description": "用户要求分析第3批次的稳定性"
    }
    print(f"GPT工具调用: {json.dumps(tool_call, ensure_ascii=False)[:100]}...")
    
    # 步骤2: 系统执行工具调用
    print("\n🔹 步骤2: 系统执行工具调用")
    try:
        tool_result = dispatch_gpt_response(json.dumps(tool_call, ensure_ascii=False))
        
        if tool_result["type"] == "tool_result":
            print("✅ 工具执行成功!")
            tool_data = tool_result["data"]
            print(f"数据量: {len(json.dumps(tool_data, ensure_ascii=False))} 字符")
            print(f"分析类型: {tool_data.get('analysis_type', '')}")
            print(f"分析指标数: {len(tool_data.get('analysis_results', {}))}")
        else:
            print(f"❌ 工具执行失败: {tool_result.get('content', '')}")
            return False
            
    except Exception as e:
        print(f"❌ 工具调用异常: {str(e)}")
        return False
    
    # 步骤3: 模拟GPT分析工具结果
    print("\n🔹 步骤3: GPT分析工具结果")
    gpt_analysis = simulate_gpt_analysis_response(tool_data)
    print("GPT分析响应生成成功!")
    
    try:
        analysis_json = json.loads(gpt_analysis)
        summary = analysis_json["analysis_summary"]
        
        print(f"📁 数据源: {summary['data_source']}")
        print("🔍 关键发现:")
        for i, finding in enumerate(summary["key_findings"], 1):
            print(f"  {i}. {finding}")
        print(f"📊 整体评价: {summary['overall_assessment']}")
        print("💡 建议:")
        for i, rec in enumerate(summary["recommendations"], 1):
            print(f"  {i}. {rec}")
            
    except Exception as e:
        print(f"❌ GPT分析结果解析失败: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ 完整工作流程测试成功!")
    print("用户体验: 请求 -> 工具执行 -> 智能分析 -> 结构化结果")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_complete_workflow()