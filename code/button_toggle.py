class ButtonToggle:
    def __init__(self):
        self.state = "Start"
        self.camera_on = False

    def toggle(self):
        if self.state == "Start":
            self.state = "Stop"
            self.camera_on = True
        else:
            self.state = "Start"
            self.camera_on = False
        return self.state, self.camera_on

