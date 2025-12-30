from g15 import *
import threading
from signal import signal, SIGINT
from winreg import OpenKey, EnumValue, HKEY_CURRENT_USER
from subprocess import check_output
from datetime import datetime
from time import sleep

HWND_BROADCAST = 0xFFFF
WM_SYSCOMMAND = 0x0112
SC_MONITORPOWER = 0xF170
def monitor_sleep() -> None:
    windll.user32.PostMessageW(
        HWND_BROADCAST,
        WM_SYSCOMMAND,
        SC_MONITORPOWER,
        2
    )

dis_command = ["powercfg", "-requests"] # Requires administrator privileges
dis_compare_string = "DISPLAY:\nNone."
dis_compare_len = len(dis_compare_string)
def get_display_lock_status() -> bool:
    return not check_output(dis_command, text=True)[:dis_compare_len] == dis_compare_string

def format_seconds(seconds) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = int(round(seconds % 60))
    if remaining_seconds == 60:
        minutes += 1
        remaining_seconds = 0
    formatted_time = "{:02d}:{:02d}:{:02d}".format(hours, minutes, remaining_seconds)
    return formatted_time

class LASTINPUTINFO(Structure):
    _fields_ = [("cbSize", wintypes.UINT),
                ("dwTime", wintypes.DWORD)]
user32 = windll.user32
kernel32 = windll.kernel32

def get_last_input_time() -> str:
    lii = LASTINPUTINFO()
    lii.cbSize = 8

    if user32.GetLastInputInfo(byref(lii)):
        system_uptime = kernel32.GetTickCount() & 0xFFFFFFFF
        last_input_tick = lii.dwTime

        if system_uptime < last_input_tick:
            elapsed_ms = (system_uptime + (0xFFFFFFFF + 1)) - last_input_tick
        else:
            elapsed_ms = system_uptime - last_input_tick

        return format_seconds(round(elapsed_ms / 1000.0))
    else:
        raise WinError(get_last_error())

INBOX_IDENTIFIER = "Inbox ("
EnumWindows = user32.EnumWindows
EnumWindowsProc = WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
GetWindowTextW = user32.GetWindowTextW
GetWindowTextLengthW = user32.GetWindowTextLengthW
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
IsWindowVisible = user32.IsWindowVisible

def get_inbox_number() -> dict:
    titles = {}
    def callback(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLengthW(hwnd)

            if length >= 11:
                pid = wintypes.DWORD()
                GetWindowThreadProcessId(hwnd, byref(pid))
                
                buffer = c_u_b(length + 1)
                GetWindowTextW(hwnd, buffer, length + 1)
                val = buffer.value
                
                titles[val[:7]] = val[:11]
                
        return True

    EnumWindows(EnumWindowsProc(callback), 0)
    return titles.get(INBOX_IDENTIFIER)
        
sensor_cond = "Sensor"
label_cond = "Label"
value_cond_1 = "Value"
value_cond_2 = "Raw"
def get_hardware_stats() -> dict:
    hw = {}
    key_path = r"SOFTWARE\HWiNFO64\VSB"

    while True:
        try:
            with OpenKey(HKEY_CURRENT_USER, key_path) as key:
                index = 0
                curr_m = None
                curr_label = None
                
                while True:
                    try:
                        value_name, value_data, _ = EnumValue(key, index)
                        index += 1
                        
                        if value_name.startswith(sensor_cond):
                            curr_m = value_data
                            if curr_m not in hw:
                                hw[curr_m] = {}
                            continue
                        
                        if value_name.startswith(label_cond):
                            curr_label = value_data
                        
                        if value_name.startswith(value_cond_1) and value_cond_2 not in value_name:
                            hw[curr_m][curr_label] = value_data
                    except OSError:
                        break
            break
        except:
            # hwinfo64 sensors isnt open or there are no gadget entries enabled
            sleep(0.33)
            continue
    
    return hw

def main():
    LCD = Logi_LCD("ROFLOS", LOGI_LCD_TYPE_MONO)

    threads = []
    event = threading.Event()
    event.set()
    aux_event = threading.Event()
    
    def signal_handler(signum, frame) -> None:
        event.clear()
        print("Exiting...", end='\r')
        for thread in threads:
            thread.join()
        exit(0)
    signal(SIGINT, signal_handler)
    
    master = {}
    
    def update_master(master, event, aux_event) -> None:
        hwinfo = 'hwinfo'
        misc = 'misc'
        inbox = 'inbox'
        idle = 'idle'

        master[misc] = {}
        master[hwinfo] = get_hardware_stats()
        master[misc][inbox] = get_inbox_number()
        master[misc][idle] = get_last_input_time()
        aux_event.set()

        while event.is_set():
            master[hwinfo] = get_hardware_stats()
            master[misc][inbox] = get_inbox_number()
            master[misc][idle] = get_last_input_time()
            sleep(0.5)
            
    threads.append(threading.Thread(target=update_master, args=(master, event, aux_event)))
    
    def update_rows(master:dict, LCD: Logi_LCD, event:threading.Event, aux_event:threading.Event) -> None:
        hwinfo = 'hwinfo'
        misc = 'misc'
        inbox = 'inbox'
        idle = 'idle'
        aux_event.wait()
        aux_event.clear()
        
        gpu_master_key = "GPU [#0]: NVIDIA GeForce RTX 4080: ASUS TUF RTX 4080 GAMING OC"
        cpu_master_key_enhanced = "CPU [#0]: AMD Ryzen 7 7800X3D: Enhanced"
        cpu_master_key = "CPU [#0]: AMD Ryzen 7 7800X3D"

        gpu_hotspot_key = "GPU Hot Spot Temperature"
        gpu_temp_key = "GPU Temperature"
        gpu_clock_key = "GPU Clock"
        gpu_usage_key = "GPU Core Load"
        gpu_pwr_key = "GPU 16-pin HVPWR Power"
        gpu_voltage_key = "GPU Core Voltage"

        cpu_usage_key = "Total CPU Usage"
        cpu_clocks_key = "Core Clocks"
        cpu_tctl_tdie_key = "CPU (Tctl/Tdie)"
        # cpu_die_avg_key = "CPU Die (average)"
        cpu_package_power_key = "CPU Package Power"
        cpu_voltage_key = "CPU VDDCR_VDD Voltage (SVI3 TFN)"

        GPU_HOTSPOT = lambda data: data[gpu_hotspot_key].replace(' ', '')
        GPU_TEMP = lambda data: data[gpu_temp_key].replace(' ', '')
        GPU_CLOCK = lambda data: data[gpu_clock_key].replace(' ', '')
        GPU_USAGE = lambda data: data[gpu_usage_key].replace(' ', '')
        GPU_PWR = lambda data: data[gpu_pwr_key].replace(' ', '')
        GPU_CORE_VOLTAGE = lambda data: data[gpu_voltage_key].replace(' ', '')

        CPU_USAGE = lambda data: data[cpu_usage_key].replace(' ', '')
        CPU_CLOCKS = lambda data: data[cpu_clocks_key].replace(' ', '')
        CPU_TCTL_TDIE = lambda data: data[cpu_tctl_tdie_key].replace(' ', '')
        # CPU_DIE_AVG = lambda data: data[cpu_die_avg_key].replace(' ', '')
        CPU_PACKAGE_POWER = lambda data: data[cpu_package_power_key].replace(' ', '')
        CPU_VOLTAGE = lambda data: data[cpu_voltage_key].replace(' ', '')
        
        while event.is_set():
            gpu_data = master[hwinfo][gpu_master_key]
            cpu_data = {**master[hwinfo][cpu_master_key_enhanced], **master[hwinfo][cpu_master_key]}
            
            LCD.mono_set_text(0, f"{master[misc][inbox]} {CPU_PACKAGE_POWER(cpu_data)} {GPU_PWR(gpu_data)}")
            
            LCD.mono_set_text(1, f"{CPU_TCTL_TDIE(cpu_data)} {CPU_USAGE(cpu_data)} {CPU_CLOCKS(cpu_data)} {CPU_VOLTAGE(cpu_data)}")
            
            LCD.mono_set_text(2, f"{GPU_HOTSPOT(gpu_data)} {GPU_TEMP(gpu_data)} {GPU_USAGE(gpu_data)} {GPU_CLOCK(gpu_data)}")
            
            LCD.mono_set_text(3, f"{master[misc][idle]} {get_display_lock_status()} {GPU_CORE_VOLTAGE(gpu_data)} {datetime.now().strftime('%H:%M:%S')}")
            
            LCD.update()
            
            if (LCD.is_button_pressed(LOGI_LCD_MONO_BUTTON_0)):
                monitor_sleep()
            
            sleep(1)
            
    threads.append(threading.Thread(target=update_rows, args=(master, LCD, event, aux_event)))
    
    for thread in threads:
        thread.start()
    
    while event.is_set():
        sleep(1)
    exit(0)
    
main()
