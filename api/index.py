from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# 主页测试路由
@app.route('/')
def home():
    return "Webhook server is running!"

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
    ticker = data.get('ticker', '未知')  # 使用 TradingView 数据中的 ticker 字段
    formatted_content = f"{ticker}交易消息：做空！"
    
    # 替换 JSON 模板中的 content
    json_template['text']['content'] = formatted_content

    # 打印替换后的 JSON
    print(f"Formatted JSON: {json_template}")

    # 向其他服务器发送 POST 请求
    target_url = "https://oapi.dingtalk.com/robot/send?access_token=5bc7e0577062bb4bacc9959f566d77341c78db1c03b66a1f3431d23f7c647bf4"
    try:
        response = requests.post(target_url, json=json_template)
        response.raise_for_status()  # 检查请求是否成功
        return jsonify({"status": "success", "formatted_data": json_template, "forwarded_status_code": response.status_code}), 200
    except requests.RequestException as e:
        print(f"Error forwarding data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
