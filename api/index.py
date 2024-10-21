from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# 主页测试路由
@app.route('/')
def home():
    return "Webhook server is running!"

# 测dwx连通性
@app.route('/dwx')
def dwx():
    try:
        # 发起GET请求到指定的地址，并设置超时时间为2秒
        response = requests.get('http://118.25.137.220:5000/', timeout=2)
        
        # 检查响应状态码，确保请求成功
        if response.status_code == 200:
            # 打印响应内容
            print(f"请求成功，返回内容: {response.text}")
            return jsonify({'status': 'success', 'data': response.text}), 200
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return jsonify({'status': 'error', 'message': f'Failed with status code {response.status_code}'}), response.status_code

    except requests.exceptions.Timeout:
        # 处理请求超时的情况
        print("请求超时")
        return jsonify({'status': 'error', 'message': 'Request timed out'}), 504

    except requests.exceptions.RequestException as e:
        # 处理其他请求错误
        print(f"请求出错: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# 接收 TradingView 的 Webhook 消息
@app.route('/webhook', methods=['POST'])
def webhook():
    # 获取 POST 请求中的 JSON 数据
    data = request.json
    
    if data is None:
        return jsonify({"error": "No data received"}), 400

    # 打印接收到的数据
    print(f"Received data: {data}")

    # 固定格式的 JSON 模板
    json_template = {
        "at": {"isAtAll": True},
        "text": {"content": "{{ticker}}交易消息：做空！"},
        "msgtype": "text"
    }

    # 替换 content 字段中的占位符
    # 这里假设 TradingView 消息中有 `ticker` 字段
    ticker = data.get('ticker', '未知')  # 使用 TradingView 发来的数据
    order_type_str = data.get('type', '未知')
    order_type = 'buy' if order_type_str == 'Long' else 'sell'
    type_desc = '做多' if order_type_str == 'Long' else '做空'
    enterPrice = data.get('enterPrice', '未知')
    tp = data.get('TP', '未知')
    sl = data.get('SL', '未知')
    rpt = data.get('rpt', '未知')
    formatted_content = f"{ticker}交易消息: {type_desc}\n入场价: {enterPrice}\n止盈价: {tp}\n止损价: {sl}\n每笔订单风险: {rpt}!"
    
    # 替换 JSON 模板中的 content
    json_template['text']['content'] = formatted_content

    # 打印替换后的 JSON
    print(f"Formatted JSON: {json_template}")

    # dwx_connect trade 地址发送 POST 请求
    dwx_connect_trade_url = "http://118.25.137.220:5000/open_order"
    try:
        trade_json = {
            "symbol": ticker,
            "enter_price": enterPrice,
            "order_type": order_type,
            "sl": sl,
            "tp": tp,
            "rpt": rpt
        }
        response = requests.post(dwx_connect_trade_url, json=trade_json)
        response.raise_for_status()  # 检查请求是否成功
        print(f"Success forwarding code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error forwarding data: {e}")

    # 向钉钉机器人 webhook 地址发送 POST 请求
    dingding_url = "https://oapi.dingtalk.com/robot/send?access_token=5bc7e0577062bb4bacc9959f566d77341c78db1c03b66a1f3431d23f7c647bf4"
    try:
        response = requests.post(dingding_url, json=json_template)
        response.raise_for_status()  # 检查请求是否成功
        print(f"Success forwarding code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error forwarding data: {e}")

    return "process msg finished."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
