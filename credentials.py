"""密钥只留在本地后端；Windows DPAPI 加密绑定当前 Windows 用户。"""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path

from dualmind import ModelError


class Blob(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]


def dpapi(data: bytes, decrypt: bool = False) -> bytes:
    if os.name != "nt":
        raise ModelError("应用内加密保存目前仅支持 Windows；其他系统请使用环境变量。")
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    function = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                         ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise ModelError("Windows 密钥加密或解密失败，请在设置中重新保存 Key。")
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel.LocalFree(ctypes.cast(target.data, ctypes.c_void_p))


def persistent_environment() -> tuple[str | None, str]:
    if os.name == "nt":
        import winreg
        for hive, path, label in (
            (winreg.HKEY_CURRENT_USER, "Environment", "Windows 用户环境变量"),
            (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", "Windows 系统环境变量"),
        ):
            try:
                with winreg.OpenKey(hive, path) as registry:
                    value, _ = winreg.QueryValueEx(registry, "GEMINI_API_KEY")
                    if isinstance(value, str) and value.strip():
                        return value.strip(), label
            except OSError:
                pass
    return None, "未配置"


class Credentials:
    def __init__(self, root: Path):
        self.path = Path(root) / "gemini-key.dpapi"

    def read(self) -> tuple[str | None, str]:
        if self.path.exists():
            try:
                return dpapi(self.path.read_bytes(), decrypt=True).decode("utf-8"), "应用内 · Windows 加密保存"
            except (OSError, UnicodeError) as exc:
                raise ModelError("读取本地加密密钥失败，请重新保存 Key。") from exc
        value = os.environ.get("GEMINI_API_KEY", "").strip()
        if value:
            return value, "启动进程环境变量"
        return persistent_environment()

    def get_key(self) -> str | None:
        return self.read()[0]

    def status(self) -> dict:
        try:
            key, source = self.read()
            return {"configured": bool(key), "source": source, "error": ""}
        except ModelError as exc:
            return {"configured": False, "source": "需重新配置", "error": str(exc)}

    def save(self, value: str):
        value = value.strip()
        if not 20 <= len(value) <= 256 or any(ch.isspace() for ch in value):
            raise ValueError("Key 格式不正确，请粘贴完整的 Gemini API Key。")
        encrypted = dpapi(value.encode("utf-8"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_bytes(encrypted)
        temporary.replace(self.path)
