import serial

class instru_serial(serial.Serial):

    def ask(self,cmd):
        self.write((cmd).encode("utf-8"))
        return(self.readline().decode())

    def query(self,cmd):
        return self.ask(cmd)
        
    def write(self,cmd):
        self.write((cmd).encode("utf-8"))