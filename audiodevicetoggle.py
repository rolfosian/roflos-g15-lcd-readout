import ctypes
from ctypes import POINTER, byref, wintypes

HRESULT = ctypes.c_long

CLSCTX_ALL = 23
eRender = 0
eConsole = 0
DEVICE_STATE_ACTIVE = 0x1
STGM_READ = 0

# GUID
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8)
    ]

# PROPERTYKEY
class PROPERTYKEY(ctypes.Structure):
    _fields_ = [("fmtid", GUID), ("pid", wintypes.DWORD)]

# PROPVARIANT (LPWSTR only)
class PROPVARIANT(ctypes.Structure):
    _fields_ = [
        ("vt", wintypes.USHORT),
        ("w1", wintypes.USHORT),
        ("w2", wintypes.USHORT),
        ("w3", wintypes.USHORT),
        ("pwszVal", wintypes.LPWSTR)
    ]

VT_LPWSTR = 31

PKEY_Device_FriendlyName = PROPERTYKEY(
    GUID(0xA45C254E,0xDF1C,0x4EFD,(ctypes.c_ubyte*8)(0x80,0x20,0x67,0xD1,0x46,0xA8,0x50,0xE0)),
    14
)

CLSID_MMDeviceEnumerator = GUID(
    0xBCDE0395,0xE52F,0x467C,(ctypes.c_ubyte*8)(0x8E,0x3D,0xC4,0x57,0x92,0x91,0x69,0x2E)
)

IID_IMMDeviceEnumerator = GUID(
    0xA95664D2,0x9614,0x4F35,(ctypes.c_ubyte*8)(0xA7,0x46,0xDE,0x8D,0xB6,0x36,0x17,0xE6)
)

CLSID_PolicyConfigClient = GUID(
    0x870AF99C,0x171D,0x4F9E,(ctypes.c_ubyte*8)(0xAF,0x0D,0xE6,0x3D,0xF4,0x0C,0x2B,0xC9)
)

IID_IPolicyConfig = GUID(
    0xF8679F50,0x850A,0x41CF,(ctypes.c_ubyte*8)(0x9C,0x72,0x43,0x0F,0x29,0x02,0x90,0xC8)
)

# Interfaces

class IMMDeviceEnumeratorVtbl(ctypes.Structure):
    _fields_ = [
        ("QueryInterface", ctypes.c_void_p),
        ("AddRef", ctypes.c_void_p),
        ("Release", ctypes.c_void_p),
        ("EnumAudioEndpoints", ctypes.WINFUNCTYPE(HRESULT, ctypes.c_void_p, ctypes.c_int, wintypes.DWORD, ctypes.c_void_p)),
        ("GetDefaultAudioEndpoint", ctypes.WINFUNCTYPE(HRESULT, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)),
    ]

class IMMDeviceEnumerator(ctypes.Structure):
    _fields_ = [("lpVtbl", POINTER(IMMDeviceEnumeratorVtbl))]

class IMMDeviceCollectionVtbl(ctypes.Structure):
    _fields_ = [
        ("QueryInterface", ctypes.c_void_p),
        ("AddRef", ctypes.c_void_p),
        ("Release", ctypes.c_void_p),
        ("GetCount", ctypes.WINFUNCTYPE(HRESULT, ctypes.c_void_p, POINTER(ctypes.c_uint))),
        ("Item", ctypes.WINFUNCTYPE(HRESULT, ctypes.c_void_p, ctypes.c_uint, POINTER(ctypes.c_void_p))),
    ]

class IMMDeviceCollection(ctypes.Structure):
    _fields_ = [("lpVtbl", POINTER(IMMDeviceCollectionVtbl))]

class IMMDeviceVtbl(ctypes.Structure):
    _fields_ = [
        ("QueryInterface", ctypes.c_void_p),
        ("AddRef", ctypes.c_void_p),
        ("Release", ctypes.c_void_p),
        ("Activate", ctypes.c_void_p),
        ("OpenPropertyStore", ctypes.WINFUNCTYPE(HRESULT, ctypes.c_void_p, wintypes.DWORD, POINTER(ctypes.c_void_p))),
        ("GetId", ctypes.WINFUNCTYPE(HRESULT, ctypes.c_void_p, POINTER(wintypes.LPWSTR))),
    ]

class IMMDevice(ctypes.Structure):
    _fields_ = [("lpVtbl", POINTER(IMMDeviceVtbl))]

class IPropertyStoreVtbl(ctypes.Structure):
    _fields_ = [
        ("QueryInterface", ctypes.c_void_p),
        ("AddRef", ctypes.c_void_p),
        ("Release", ctypes.c_void_p),
        ("GetCount", ctypes.c_void_p),
        ("GetAt", ctypes.c_void_p),
        ("GetValue", ctypes.WINFUNCTYPE(HRESULT, ctypes.c_void_p, POINTER(PROPERTYKEY), POINTER(PROPVARIANT))),
    ]

class IPropertyStore(ctypes.Structure):
    _fields_ = [("lpVtbl", POINTER(IPropertyStoreVtbl))]

class IPolicyConfigVtbl(ctypes.Structure):
    _fields_ = [
        ("QueryInterface", ctypes.c_void_p),
        ("AddRef", ctypes.c_void_p),
        ("Release", ctypes.c_void_p),
        *[(f"pad{i}", ctypes.c_void_p) for i in range(10)],
        ("SetDefaultEndpoint", ctypes.WINFUNCTYPE(HRESULT, ctypes.c_void_p, wintypes.LPCWSTR, ctypes.c_int)),
    ]

class IPolicyConfig(ctypes.Structure):
    _fields_ = [("lpVtbl", POINTER(IPolicyConfigVtbl))]

def toggle_audio_if_2():
    ole32 = ctypes.WinDLL("ole32")
    # Init COM
    ole32.CoInitialize(None)

    # Create enumerator
    pEnumerator = POINTER(IMMDeviceEnumerator)()
    ole32.CoCreateInstance(byref(CLSID_MMDeviceEnumerator), None, CLSCTX_ALL, byref(IID_IMMDeviceEnumerator), byref(pEnumerator))

    # Get collection
    pCollection = ctypes.c_void_p()
    pEnumerator.contents.lpVtbl.contents.EnumAudioEndpoints(pEnumerator, eRender, DEVICE_STATE_ACTIVE, byref(pCollection))
    pCollection = ctypes.cast(pCollection, POINTER(IMMDeviceCollection))

    # Count
    count = ctypes.c_uint()
    pCollection.contents.lpVtbl.contents.GetCount(pCollection, byref(count))

    # print("Device count:", count.value)

    device_ids = []
    device_names = []

    # Enumerate
    for i in range(count.value):
        pDevice = ctypes.c_void_p()
        pCollection.contents.lpVtbl.contents.Item(pCollection, i, byref(pDevice))

        dev = ctypes.cast(pDevice, POINTER(IMMDevice))

        # Name
        pStore = ctypes.c_void_p()
        dev.contents.lpVtbl.contents.OpenPropertyStore(dev, STGM_READ, byref(pStore))
        store = ctypes.cast(pStore, POINTER(IPropertyStore))

        prop = PROPVARIANT()
        store.contents.lpVtbl.contents.GetValue(store, byref(PKEY_Device_FriendlyName), byref(prop))

        name = prop.pwszVal if prop.vt == VT_LPWSTR else "Unknown"
        # print(i, name)

        # ID
        pId = wintypes.LPWSTR()
        dev.contents.lpVtbl.contents.GetId(dev, byref(pId))

        device_ids.append(pId)
        device_names.append(name)

    if len(device_ids) == 2:
        # Get current default
        pDefault = ctypes.c_void_p()
        pEnumerator.contents.lpVtbl.contents.GetDefaultAudioEndpoint(pEnumerator, eRender, eConsole, byref(pDefault))

        dev_default = ctypes.cast(pDefault, POINTER(IMMDevice))
        cur_id = wintypes.LPWSTR()
        dev_default.contents.lpVtbl.contents.GetId(dev_default, byref(cur_id))

        # Choose other device
        target = device_ids[1] if cur_id.value == device_ids[0].value else device_ids[0]

        # PolicyConfig
        pPolicy = ctypes.c_void_p()
        ole32.CoCreateInstance(byref(CLSID_PolicyConfigClient), None, CLSCTX_ALL, byref(IID_IPolicyConfig), byref(pPolicy))
        policy = ctypes.cast(pPolicy, POINTER(IPolicyConfig))

        for role in (0, 1, 2):
            policy.contents.lpVtbl.contents.SetDefaultEndpoint(policy, target, role)

        # print("Switched default to:", target.value)
    # else:
    #     print("Toggle requires exactly 2 devices")
        
    ole32.CoUninitialize()