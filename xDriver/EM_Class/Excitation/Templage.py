

class Template:
    def __init__(self,tunnel = "socket", address = ""):
        if tunnel == "socket":
            print("Template: 使用 Socket 方式连接，地址：", address)
            # 建立 Socket 连接
        elif tunnel == "visa":
            print("Template: 使用 VISA 方式连接，地址：", address)
        else:
            print("Template: 未知的连接方式，使用默认设置")