import socket

class instru_socket(socket.socket):

    # def ask(self,cmd):
    #     self.send((cmd+"\r\n").encode("utf-8"))
    #     msg=self.recv(1024).decode()
    #     while(msg.find("\n")==False):
    #         msg+=self.recv(1024).decode()
    #     return(msg)

    def ask(self,cmd):
        self.send((cmd+"\n").encode("utf-8"))
        #读取所有返回内容，直到缓冲区为空
        msg = ""
        while True:
            part = self.recv(1024).decode()
            msg += part
            if len(part) < 1024:
                break
        return(msg)
    
    def query(self,cmd):
        return self.ask(cmd)
        
    def write(self,cmd):
        self.send((cmd+"\n").encode("utf-8"))
    