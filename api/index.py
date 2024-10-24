from flask import Flask, request, jsonify
import requests
import threading

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
        response = requests.get('http://118.25.137.220:8080/hello', timeout=2)
        
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


# 处理钉钉请求的函数
def send_to_dingding(json_template):
    dingding_url = "https://oapi.dingtalk.com/robot/send?access_token=5bc7e0577062bb4bacc9959f566d77341c78db1c03b66a1f3431d23f7c647bf4"
    try:
        response = requests.post(dingding_url, json=json_template)
        response.raise_for_status()  # 检查请求是否成功
        print(f"Success forwarding to DingDing. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error forwarding data to DingDing: {e}")

# 处理 dwx_connect_trade 请求的函数
def send_to_dwx_connect_trade(trade_json):
    dwx_connect_trade_url = "http://118.25.137.220:8080/open_order"
    try:
        response = requests.post(dwx_connect_trade_url, json=trade_json, timeout=2)
        print(f"Success forwarding to DWX connect trade. Status code: {response.status_code}")
    except requests.exceptions.Timeout:
        print("请求超时")
    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")


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
    ticker = data.get('ticker', '未知')  # 使用 TradingView 发来的数据
    order_type_str = data.get('type', '未知')
    order_type = 'buy' if order_type_str == 'Long' else 'sell'
    type_desc = '做多' if order_type_str == 'Long' else '做空'
    enter_price = data.get('enterPrice', '未知')
    tp = data.get('TP', '未知')
    sl = data.get('SL', '未知')
    rpt = data.get('rpt', '未知')
    formatted_content = f"{ticker}交易消息: {type_desc}\n入场价: {enter_price}\n止盈价: {tp}\n止损价: {sl}\n每笔订单风险: {rpt}!"

    # 替换 JSON 模板中的 content
    json_template['text']['content'] = formatted_content

    # 打印替换后的 JSON
    print(f"Formatted JSON: {json_template}")

    # 准备 trade_json
    trade_json = {
        "symbol": ticker,
        "price": enter_price,
        "orderType": order_type,
        "stopLoss": sl,
        "takeProfit": tp,
        "rpt": rpt
    }
    print(f"trade_json: {trade_json}")

    # 使用线程分别处理两个 POST 请求
    thread_dingding = threading.Thread(target=send_to_dingding, args=(json_template,))
    thread_dwx_trade = threading.Thread(target=send_to_dwx_connect_trade, args=(trade_json,))

    # 启动线程
    thread_dingding.start()
    thread_dwx_trade.start()

    # 等待两个线程执行完毕
    thread_dingding.join()
    thread_dwx_trade.join()

    return "process msg finished."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
