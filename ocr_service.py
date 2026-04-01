"""
知识星球OCR识别服务模块
使用智谱AI GLM-4V多模态大模型识别知识星球截图中的到期时间
"""
import re
import json
import base64
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from zhipuai import ZhipuAI
from config import Config

logger = logging.getLogger(__name__)

# GLM-4V客户端（延迟初始化）
_glm_client = None

def get_glm_client():
    """获取GLM-4V客户端实例（单例模式）"""
    global _glm_client
    if _glm_client is None:
        try:
            _glm_client = ZhipuAI(api_key=Config.GLM_API_KEY)
            logger.info("GLM-4V客户端初始化成功")
        except Exception as e:
            logger.error(f"GLM-4V客户端初始化失败: {str(e)}")
            raise
    return _glm_client

# 日期匹配正则表达式
DATE_PATTERNS = [
    r'(\d{4})[/\-年](\d{1,2})[/\-月](\d{1,2})',  # 2026/7/16, 2026-7-16, 2026年7月16日
    r'截至.*?(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})',  # 截至权限到期至2026/7/16
    r'到期.*?(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})',  # 到期至2026/7/16
    r'有效期.*?(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})',  # 有效期至2026/7/16
]

# 永久会员关键字
PERMANENT_KEYWORDS = ['永久', '终身', '无限期', '无期限']

def image_to_base64(image_path):
    """将图片转换为base64编码"""
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode('utf-8')

def recognize_planet_screenshot(image_path):
    """
    识别知识星球截图并提取到期时间
    
    Args:
        image_path (str): 截图文件路径
    
    Returns:
        dict: {
            'success': bool,              # 是否成功识别
            'raw_text': str,              # OCR原始文本
            'expiry_date': datetime,      # 提取的到期日期（永久会员为None）
            'is_permanent': bool,         # 是否为永久会员
            'confidence': float,          # 识别置信度(0-1)
            'duration_months': int,       # 权限时长（月数，永久会员为None）
            'error': str                  # 错误信息（如有）
        }
    """
    try:
        # 将图片转换为base64
        image_base64 = image_to_base64(image_path)
        
        # 调用GLM-4V进行图像理解
        client = get_glm_client()
        
        # 构造提示词，引导模型提取或推算到期时间
        prompt = """请仔细识别这张图片中的所有文字信息。这是一张与"AI临床医工交叉"知识星球相关的截图。

图片可能是以下任一类型：
1. 微信/支付宝支付凭证（显示支付时间、金额、商品名等）
2. 知识星球会员页面（直接显示到期日期）

请按以下规则提取到期日期（expiry_date）：
- 如果图中直接显示了到期日期/有效期，直接提取该日期
- 如果图中只有支付时间（如"支付时间: 2025年12月29日"），则到期日期 = 支付时间 + 12个月（知识星球为年费制）
- 日期统一用 YYYY-MM-DD 格式

请以JSON格式返回：
{
    "expiry_date": "YYYY-MM-DD",
    "raw_text": "图中识别到的关键文字（支付时间、金额、商品名、到期日期等）"
}

只返回JSON。"""
        
        response = client.chat.completions.create(
            model="glm-4v-flash",  # 使用glm-4v-flash模型，速度快且准确
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            temperature=0.1,  # 降低温度以提高准确性
            max_tokens=500
        )
        
        # 解析GLM-4V返回的结果
        result_text = response.choices[0].message.content
        logger.info(f"GLM-4V原始返回: {result_text}")
        
        # 提取JSON部分（有些模型可能会在JSON前后加说明文字）
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result_json = json.loads(json_match.group())
        else:
            logger.warning("未能从GLM-4V返回中提取JSON，尝试直接解析")
            result_json = json.loads(result_text)
        
        raw_text = result_json.get('raw_text', '')
        # raw_text可能是dict（模型返回了结构化数据），统一转为字符串
        if isinstance(raw_text, dict):
            raw_text = json.dumps(raw_text, ensure_ascii=False)
        expiry_date_str = result_json.get('expiry_date')
        
        # 解析到期日期
        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
            except ValueError:
                # 如果GLM返回的日期格式不标准，尝试用正则提取
                logger.warning(f"日期格式不标准: {expiry_date_str}，尝试正则提取")
                expiry_date = extract_date_from_text(raw_text)

        # 如果GLM没有成功提取，再尝试用正则从raw_text中提取
        if not expiry_date and raw_text:
            logger.info("GLM未成功提取日期，使用正则表达式尝试提取")
            expiry_date = extract_date_from_text(raw_text)

        # 兜底：如果识别到的日期已过期，说明模型可能返回了支付日期而非到期日期
        # 知识星球为年费制，自动加12个月作为推算到期日期
        if expiry_date and expiry_date < datetime.now():
            logger.info(f"识别日期 {expiry_date.strftime('%Y-%m-%d')} 已过期，推算为支付日期，自动+12个月")
            expiry_date = expiry_date + relativedelta(months=12)
        
        # 计算置信度
        confidence = 0.0
        if expiry_date:
            confidence = 0.9  # GLM-4V视觉能力强，置信度较高
        else:
            confidence = 0.4
        
        # 计算会员时长
        duration_months = None
        if expiry_date:
            current_time = datetime.now()
            duration_months = calculate_membership_duration(current_time, expiry_date)
        
        return {
            'success': True,
            'raw_text': raw_text,
            'expiry_date': expiry_date,
            'is_permanent': False,        # 始终为False
            'confidence': confidence,
            'duration_months': duration_months,
            'error': None
        }
        
    except FileNotFoundError:
        logger.error(f"文件不存在: {image_path}")
        return {
            'success': False,
            'raw_text': '',
            'expiry_date': None,
            'is_permanent': False,
            'confidence': 0.0,
            'duration_months': None,
            'error': f"文件不存在: {image_path}"
        }
    except json.JSONDecodeError as e:
        logger.error(f"GLM-4V返回结果JSON解析失败: {str(e)}")
        return {
            'success': False,
            'raw_text': '',
            'expiry_date': None,
            'is_permanent': False,
            'confidence': 0.0,
            'duration_months': None,
            'error': f"GLM-4V返回结果解析失败: {str(e)}"
        }
    except Exception as e:
        logger.error(f"OCR识别失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'raw_text': '',
            'expiry_date': None,
            'is_permanent': False,
            'confidence': 0.0,
            'duration_months': None,
            'error': f"OCR识别失败: {str(e)}"
        }

def extract_date_from_text(text):
    """
    从OCR文本中提取日期（正则表达式备用方案）
    
    支持格式：
    - "截至权限到期至2026/7/16"
    - "2026年7月16日"
    - "2026-07-16"
    
    Args:
        text (str): OCR识别的文本
    
    Returns:
        datetime对象 或 None
    """
    # 尝试提取日期
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            try:
                # 提取年月日
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                
                # 构造日期对象
                expiry_date = datetime(year, month, day)
                
                logger.info(f"成功提取到期日期: {expiry_date.strftime('%Y-%m-%d')}")
                return expiry_date
            except (ValueError, IndexError) as e:
                logger.warning(f"日期解析失败: {match.group(0)}, 错误: {str(e)}")
                continue
    
    # 未能提取到日期
    logger.warning("未能从文本中提取到期日期")
    return None

def calculate_membership_duration(start_date, expiry_date):
    """
    计算会员时长（月数）
    
    Args:
        start_date (datetime): 开始时间（申请时间）
        expiry_date (datetime): 到期时间
    
    Returns:
        int: 时长（月数），向上取整
    
    Examples:
        - 申请时间: 2026-01-26, 到期时间: 2026-02-26 -> 1个月
        - 申请时间: 2026-01-26, 到期时间: 2026-04-26 -> 3个月
        - 申请时间: 2026-01-26, 到期时间: 2027-01-26 -> 12个月
    """
    # 计算月份差
    delta = relativedelta(expiry_date, start_date)
    months = delta.years * 12 + delta.months
    
    # 如果有余天，向上取整到下个月
    if delta.days > 0:
        months += 1
    
    return months

def test_ocr_service():
    """测试OCR服务（仅用于开发调试）"""
    import sys
    import io
    # 修复Windows终端GBK编码问题
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    if len(sys.argv) < 2:
        print("用法: python ocr_service.py <图片路径>")
        return

    image_path = sys.argv[1]
    result = recognize_planet_screenshot(image_path)
    
    print("=" * 60)
    print("OCR识别结果:")
    print("=" * 60)
    print(f"成功: {result['success']}")
    print(f"原始文本: {result['raw_text']}")
    print(f"到期日期: {result['expiry_date']}")
    print(f"永久会员: {result['is_permanent']}")
    print(f"置信度: {result['confidence']:.2%}")
    print(f"会员时长: {result['duration_months']} 个月" if result['duration_months'] else "会员时长: N/A")
    if result['error']:
        print(f"错误: {result['error']}")
    print("=" * 60)

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    test_ocr_service()
