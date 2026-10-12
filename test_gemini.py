"""手动真实 Gemini 短测；导入或测试发现不会发请求。"""
from credentials import Credentials
from dualmind import DATA_DIR, Settings, ask_gemini


if __name__ == "__main__":
    print(ask_gemini("请用一句中文介绍你自己。", Settings(), api_key=Credentials(DATA_DIR).get_key()))
