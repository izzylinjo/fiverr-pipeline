import win32serviceutil, win32service, win32event, subprocess, sys, os

BRIDGE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bridge.py")

class BridgeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FiverrBridge"
    _svc_display_name_ = "Fiverr Pipeline Bridge"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        subprocess.run([sys.executable, BRIDGE_SCRIPT])

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(BridgeService)
