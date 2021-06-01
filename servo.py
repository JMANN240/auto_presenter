import Adafruit_PCA9685

class Servo:
    vrange = (1350, 2100)
    hrange = (400, 2100)

    def __init__(self):
        self.pwm = Adafruit_PCA9685.PCA9685()
        self.reset()

    def update(self):
        self.pwm.set_pwm(0, 0, self.vangle)
        self.pwm.set_pwm(1, 0, self.hangle)
    
    def moveLeft(self, amount=100):
        new_angle = self.hangle - amount
        self.hangle = max(new_angle, self.hrange[0])
        self.update()
    
    def moveRight(self, amount=100):
        new_angle = self.hangle + amount
        self.hangle = min(new_angle, self.hrange[1])
        self.update()
    
    def moveDown(self, amount=100):
        new_angle = self.vangle - amount
        self.vangle = max(new_angle, self.vrange[0])
        self.update()
    
    def moveUp(self, amount=100):
        new_angle = self.vangle + amount
        self.vangle = min(new_angle, self.vrange[1])
        self.update()

    def reset(self):
        self.vangle = sum(self.vrange)//len(self.vrange)
        self.hangle = sum(self.hrange)//len(self.hrange)
        self.update()