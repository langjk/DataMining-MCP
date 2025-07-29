# test_format_robustness.py
# 测试格式修复的健壮性

from format_fixer import FormatFixer
import json

def test_various_gpt_responses():
    """测试各种可能的GPT返回格式"""
    
    test_cases = [
        {
            "name": "标准JSON格式",
            "content": '{"action": "analysis_complete", "analysis_summary": {"data_source": "test", "key_findings": ["finding 1"], "overall_assessment": "good", "recommendations": ["rec 1"]}}',
            "expected": True
        },
        {
            "name": "带前缀文字的JSON",
            "content": '根据分析结果，返回如下：{"action": "analysis_complete", "analysis_summary": {"data_source": "test", "key_findings": ["finding 1"], "overall_assessment": "good", "recommendations": ["rec 1"]}}',
            "expected": True
        },
        {
            "name": "带后缀文字的JSON", 
            "content": '{"action": "analysis_complete", "analysis_summary": {"data_source": "test", "key_findings": ["finding 1"], "overall_assessment": "good", "recommendations": ["rec 1"]}} 以上是分析结果。',
            "expected": True
        },
        {
            "name": "多行文本分析",
            "content": '''
            根据数据分析，主要发现如下：
            1. 系统稳定性表现优秀
            2. 所有关键指标都在正常范围内
            3. 未发现显著异常
            
            整体评价：第3批次设备运行状态良好
            
            建议：
            - 继续保持当前参数设置
            - 定期监控关键指标
            - 可适当提高测试强度
            ''',
            "expected": True
        },
        {
            "name": "纯文本分析（简短）",
            "content": "数据分析完成，系统运行正常，建议继续监控。",
            "expected": True
        },
        {
            "name": "错误的JSON格式",
            "content": '{"action": "analysis_complete", "analysis_summary": {"data_source": "test"',
            "expected": False
        },
        {
            "name": "完全无关内容",
            "content": "今天天气很好，适合外出。",
            "expected": False
        }
    ]
    
    fixer = FormatFixer()
    results = []
    
    print("=" * 60)
    print("格式修复器健壮性测试")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔸 测试 {i}: {test_case['name']}")
        print(f"输入长度: {len(test_case['content'])} 字符")
        
        success, fixed_response = fixer.fix_gpt_response(test_case['content'])
        
        # 验证修复结果
        try:
            parsed = json.loads(fixed_response)
            json_valid = True
            
            # 检查是否包含必要字段
            has_action = "action" in parsed
            has_summary = "analysis_summary" in parsed
            
            if has_summary:
                summary = parsed["analysis_summary"]
                has_findings = "key_findings" in summary and len(summary["key_findings"]) > 0
                has_assessment = "overall_assessment" in summary
                has_recommendations = "recommendations" in summary
            else:
                has_findings = has_assessment = has_recommendations = False
            
            print(f"✅ JSON有效: {json_valid}")
            print(f"✅ 包含action: {has_action}")
            print(f"✅ 包含summary: {has_summary}")
            if has_summary:
                print(f"   - 关键发现: {has_findings} ({len(summary.get('key_findings', []))}个)")
                print(f"   - 整体评价: {has_assessment}")
                print(f"   - 建议: {has_recommendations} ({len(summary.get('recommendations', []))}个)")
            
            results.append({
                "test": test_case['name'],
                "success": success,
                "json_valid": json_valid,
                "complete": has_action and has_summary and has_findings
            })
            
        except Exception as e:
            print(f"❌ JSON解析失败: {str(e)}")
            results.append({
                "test": test_case['name'],
                "success": False,
                "json_valid": False,
                "complete": False
            })
    
    # 统计结果
    print("\n" + "=" * 60)
    print("测试结果统计")
    print("=" * 60)
    
    total_tests = len(results)
    successful_fixes = sum(1 for r in results if r['success'])
    valid_jsons = sum(1 for r in results if r['json_valid'])
    complete_responses = sum(1 for r in results if r['complete'])
    
    print(f"总测试数: {total_tests}")
    print(f"修复成功: {successful_fixes}/{total_tests} ({successful_fixes/total_tests*100:.1f}%)")
    print(f"JSON有效: {valid_jsons}/{total_tests} ({valid_jsons/total_tests*100:.1f}%)")
    print(f"完整响应: {complete_responses}/{total_tests} ({complete_responses/total_tests*100:.1f}%)")
    
    if valid_jsons >= total_tests * 0.8:
        print("\n🎉 格式修复器测试通过！健壮性良好。")
        return True
    else:
        print("\n⚠️ 格式修复器需要进一步优化。")
        return False

if __name__ == "__main__":
    test_various_gpt_responses()