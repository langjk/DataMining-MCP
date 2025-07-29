# test_json_serialization.py
# 测试JSON序列化问题

import json
from data_analyzer import DataAnalyzer
from csv_reader import read_csv_clean

def test_json_serialization():
    """测试数据分析结果的JSON序列化"""
    print("=" * 50)
    print("测试JSON序列化")
    print("=" * 50)
    
    file_path = "./data/测试数据正（公开）/振动（公开）/XXX-254-31Z01-01随机振动试验（公开）.csv"
    
    try:
        # 读取数据
        df, meta = read_csv_clean(file_path)
        print(f"成功读取数据: {df.shape}")
        
        # 创建分析器
        analyzer = DataAnalyzer()
        
        # 执行全面分析
        result = analyzer.comprehensive_analysis(df, time_col="时间")
        print("✅ 全面分析完成")
        
        # 尝试JSON序列化
        try:
            json_str = json.dumps(result, ensure_ascii=False, indent=2)
            print("✅ JSON序列化成功")
            print(f"JSON长度: {len(json_str)} 字符")
            
            # 测试反序列化
            parsed = json.loads(json_str)
            print("✅ JSON反序列化成功")
            
            return True
            
        except TypeError as e:
            print(f"❌ JSON序列化失败: {str(e)}")
            
            # 逐个检查结果组件
            for key, value in result.items():
                try:
                    json.dumps(value, ensure_ascii=False)
                    print(f"  ✅ {key}: 可序列化")
                except TypeError as sub_e:
                    print(f"  ❌ {key}: 序列化失败 - {str(sub_e)}")
                    
                    # 进一步分析问题字段
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            try:
                                json.dumps(sub_value, ensure_ascii=False)
                            except TypeError:
                                print(f"    ❌ {key}.{sub_key}: {type(sub_value)} - {sub_value}")
            
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_batch_comparison_json():
    """测试批次对比的JSON序列化"""
    print("\n" + "=" * 50)
    print("测试批次对比JSON序列化")
    print("=" * 50)
    
    file1 = "./data/测试数据正（公开）/振动（公开）/XXX-254-31Z01-01随机振动试验（公开）.csv"
    file2 = "./data/测试数据正（公开）/振动（公开）/XXX-254-31Z01-02随机振动试验（公开）.csv"
    
    try:
        # 读取数据
        df1, _ = read_csv_clean(file1)
        df2, _ = read_csv_clean(file2)
        
        # 创建分析器
        analyzer = DataAnalyzer()
        
        # 执行批次对比
        result = analyzer.batch_comparison(df1, df2, batch1_name="第1批次", batch2_name="第2批次")
        print("✅ 批次对比完成")
        
        # 尝试JSON序列化
        try:
            json_str = json.dumps(result, ensure_ascii=False, indent=2)
            print("✅ 批次对比JSON序列化成功")
            return True
        except TypeError as e:
            print(f"❌ 批次对比JSON序列化失败: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ 批次对比测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 测试全面分析JSON序列化
    success1 = test_json_serialization()
    
    # 测试批次对比JSON序列化
    success2 = test_batch_comparison_json()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ 所有JSON序列化测试通过！")
    else:
        print("❌ 存在JSON序列化问题")
    print("=" * 50)