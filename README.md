# roflos-g15-lcd-readout

Leveraging a few winapi features/shell commands + HWINFO64 gadget registry entries this applet shows the following on the Logitech G15 Keyboard LCD screen:

- Inbox Stats
- CPU Power Draw (Watts)
- GPU Power Draw (Watts)
- CPU Voltage
- CPU Usage Aggregate
- CPU Temperature Aggregate
- CPU Mhz Aggregate
- GPU Voltage
- GPU Temperature
- GPU Hotspot Temperature
- GPU Usage
- GPU Mhz
- User idle time in 00:00:00 format
- Whether or not there is a display lock signal that would prevent monitors from sleeping
- System time in 24 hour 00:00:00 format

Hardware keys for HWiNFO are hard coded eg `cpu_master_key = "CPU [#0]: AMD Ryzen 7 7800X3D"` - they will have to be edited on a per system basis.
