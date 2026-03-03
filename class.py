class Computer:
     def __init__(self, cpu, ram):
         self.cpu = cpu
         self.ram = ram
         print("This is a computer class")
     def config(self):
            print("The configuration is ", self.cpu, self.ram)
com1 = Computer('i5', 16)
com2 = Computer('Ryzen 5', 8)

com1.config()
com2.config()



