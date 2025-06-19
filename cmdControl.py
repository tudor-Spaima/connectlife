import asyncio
from getpass import getpass
from connectlife.api import ConnectLifeApi
from connectlife.appliance import DeviceType
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, Header, Footer
from textual.reactive import reactive

class AC1UI(App):
    CSS = """
    Screen {
        background: black;
        color: white;
    }

    Button {
        background: #2b2b2b;
        color: white;
        padding: 0 2;
        height: 3;
        width: 18;
        border: none;
    }

    Button:hover {
        background: #444444;
    }

    Button:focus {
        outline: none;
        background: #2b2b2b;
        color: white;
        border: none;
        text-style: none;
    }

    #power_on {
        background: green;
        color: black;
    }

    #power_off {
        background: crimson;
        color: black;
    }

    .tiny-row Button {
        margin-right: 1;
    }
    """

    BINDINGS = [("q", "quit", "Quit")]

    power_state = reactive("OFF")
    target_temperature = reactive("--")
    in_temperature = reactive("--")
    mode = reactive("--")

    def __init__(self, passwd: str):
        super().__init__()
        self.passwd = passwd
        self.api = None
        self.ac1 = None
        self.polling_task = None

    async def on_mount(self):
        await self.initialize_api()
        await self.refresh_status()
        self.polling_task = asyncio.create_task(self.auto_refresh())

    async def initialize_api(self):
        self.api = ConnectLifeApi(username="tudordanciu770@gmail.com", password=self.passwd)
        await self.api.login()
        devices = await self.api.get_appliances()
        self.ac1 = next((d for d in devices if d.device_nickname == "AC1" and d.device_type == DeviceType.AIRCONDITIONER), None)

    async def refresh_status(self):
        try:
            await self.api.get_appliances()
            self.ac1 = next((d for d in self.api.appliances if d.device_nickname == "AC1"), None)
            power = self.ac1.status_list.get("t_power")
            temp = self.ac1.status_list.get("t_temp")
            in_temp = self.ac1.status_list.get("f_temp_in")
            mode = self.ac1.status_list.get("t_work_mode")
            fan_value = str(self.ac1.status_list.get("t_fanspeedcv", self.ac1.status_list.get("t_fan_speed", "--")))[:1]
            fan_map = {"1": "Auto", "2": "Low", "3": "Med", "4": "High", "5": "Turbo"}
            fan = fan_map.get(str(fan_value), str(fan_value))
            swing_v = self.ac1.status_list.get("t_up_down")
            swing_h = self.ac1.status_list.get("t_swing_direction")

            self.power_state = "ON" if str(power) == "1" else "OFF"
            self.target_temperature = str(temp) if temp is not None else "--"
            self.in_temperature = str(in_temp) if in_temp is not None else "--"
            mode_map = {"1": "Auto", "2": "Cool", "3": "Dry", "4": "Fan", "5": "Heat"}
            self.mode = mode_map.get(str(mode), "--")
            self.update_ui()
            self.query_one("#status").update(
                f"[b]Power:[/b] {self.power_state}    [b]Target Temp:[/b] {self.target_temperature} °C    [b]In Temp:[/b] {self.in_temperature} °C    [b]Mode:[/b] {self.mode}    [b]Fan:[/b] {fan}  [b]Swing V:[/b] {swing_v}  [b]Swing H:[/b] {swing_h}"
            )
        except Exception as e:
            self.query_one("#status").update(f"[red]Error: {e}[/red]")

    async def auto_refresh(self):
        while True:
            await asyncio.sleep(5)
            await self.refresh_status()

    async def send_command(self, updates: dict):
        self.query_one("#status").update("[blink yellow]Waiting for AC to update...[/blink yellow]")
        await self.api.update_appliance(self.ac1.puid, updates)
        await asyncio.sleep(0.1)
        await self.refresh_status()

    def update_ui(self):
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.query_one("#status").update(
            f"[b]Power:[/b] {self.power_state}    [b]Target Temp:[/b] {self.target_temperature} °C    [b]In Temp:[/b] {self.in_temperature} °C    [b]Mode:[/b] {self.mode}    [dim]Updated: {timestamp}[/dim]"
        )

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static(
                """\
/    |  /  ]        /  ] /   \\ |    \\ |    \\   /  _]  /  ]      || |    |    ||     |/  _]
|  o  | /  / _____  /  / |     ||  _  ||  _  | /  [_  /  /|      || |     |  | |   __/  [_ 
|     |/  / |     |/  /  |  O  ||  |  ||  |  ||    _]/  / |_|  |_|| |___  |  | |  |_|    _]
|  _  /   \\_|_____/   \\_ |     ||  |  ||  |  ||   [_/   \\_  |  |  |     | |  | |   _]   [_ 
|  |  \\     |     \\     ||     ||  |  ||  |  ||     \\     | |  |  |     | |  | |  | |     |
|__|__|\\____|      \\____| \\___/ |__|__||__|__||_____|\\____| |__|  |_____||____||__| |_____|
""",
                id="ascii-art"
            ),
            Static("[blink yellow]Loading...[/blink yellow]", id="status"),
            Horizontal(
                Button("Power ON", id="power_on", variant="success"),
                Button("Power OFF", id="power_off", variant="error"),
                classes="tiny-row"
            ),
            Horizontal(
                Button("Temp +", id="temp_up"),
                Button("Temp -", id="temp_down"),
                classes="tiny-row"
            ),
            Horizontal(
                Button("Mode: Cool", id="mode_cool"),
                Button("Mode: Dry", id="mode_dry"),
                Button("Mode: Fan", id="mode_fan"),
                Button("Mode: Heat", id="mode_heat"),
                classes="tiny-row"
            ),
            Horizontal(
                Button("Swing V", id="swing_v"),
                Button("Swing H", id="swing_h"),
                Button("Fan Cycle", id="fan_cycle"),
                classes="tiny-row"
            ),
            id="controls"
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id
        try:
            if btn == "power_on":
                await self.send_command({"t_power": "1"})
            elif btn == "power_off":
                await self.send_command({"t_power": "0"})
            elif btn == "temp_up":
                temp_val = int(self.target_temperature) if self.target_temperature.isdigit() else 24
                new_temp = str(min(temp_val + 1, 30))
                self.target_temperature = new_temp
                self.update_ui()
                await self.send_command({"t_temp": new_temp})
            elif btn == "temp_down":
                temp_val = int(self.target_temperature) if self.target_temperature.isdigit() else 24
                new_temp = str(max(temp_val - 1, 16))
                self.target_temperature = new_temp
                self.update_ui()
                await self.send_command({"t_temp": new_temp})
            elif btn.startswith("mode_"):
                mode_map = {
                    "mode_cool": "2",
                    "mode_dry": "3",
                    "mode_fan": "4",
                    "mode_heat": "5",
                }
                mode_code = mode_map.get(btn)
                if mode_code:
                    self.mode = {"2": "Cool", "3": "Dry", "4": "Fan", "5": "Heat"}.get(mode_code, "--")
                    self.update_ui()
                    await self.send_command({"t_work_mode": mode_code, "t_power": "1"})
            elif btn == "fan_cycle":
                current_raw = str(self.ac1.status_list.get("t_fanspeedcv", "1"))
                current = int(current_raw) if current_raw.isdigit() else 1
                new_val = str(1 if current >= 6 else current + 1)
                await self.send_command({"t_fanspeedcv": new_val})
            elif btn == "swing_v":
                current = self.ac1.status_list.get("t_up_down", "0")
                new_state = "0" if str(current) == "1" else "1"
                await self.send_command({"t_up_down": new_state})
            elif btn == "swing_h":
                current = self.ac1.status_list.get("t_swing_direction", "0")
                new_state = "0" if str(current) == "1" else "1"
                await self.send_command({"t_swing_direction": new_state})
        except Exception as e:
            self.query_one("#status").update(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    passwd = getpass("Enter your ConnectLife password: ")
    AC1UI(passwd).run()
