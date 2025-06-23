import asyncio
from getpass import getpass
from connectlife.api import ConnectLifeApi
from connectlife.appliance import DeviceType
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, Header, Footer, LoadingIndicator, Select
from textual.reactive import reactive
from datetime import datetime

class AC1UI(App):
    CSS = """
    Screen {
        background: #203a43;
        color: #e0e0e0;
    }

    Button {
        background: #2c3e50;
        color: #ecf0f1;
        padding: 0 2;
        height: 3;
        width: 20;
        border: solid;
        text-style: bold;
    }

    Button:hover {
        background: #34495e;
        color: #1abc9c;
    }

    Button:focus {
        outline: solid;
        background: #34495e;
    }

    #power_on {
        background: #27ae60;
        color: black;
        text-style: bold;
    }

    #power_off {
        background: #c0392b;
        color: black;
        text-style: bold;
    }

    #ascii-art {
        color: #00bfff;
        text-style: bold underline;
    }

    #clock-display {
        color: #00ff00;
        text-style: bold;
        height: 3;
        width: 20;
        content-align: center middle;
        border: solid;
        background: #2c3e50;
        padding: 1;
    }

    .tiny-row Button {
        margin-right: 1;
    }

    #status-bar {
        height: 1;
        background: #1abc9c;
        width: 0%;
        transition: width 100ms;
    }

    #device_select {
        width: 12;
    }
    """

    BINDINGS = [("q", "quit", "Quit")]

    power_state = reactive("OFF")
    target_temperature = reactive("--")
    in_temperature = reactive("--")
    mode = reactive("--")
    selected_device = reactive("")

    def __init__(self, passwd: str):
        super().__init__()
        self.passwd = passwd
        self.api = None
        self.device = None
        self.polling_task = None

    async def on_mount(self):
        await self.initialize_api()
        select = self.query_one("#device_select", Select)
        select.options = [("AC1", "AC1"), ("AC2", "AC2")]
        self.selected_device = "AC1"
        select.value = self.selected_device
        self.set_interval(1, self.update_clock)
        self.polling_task = asyncio.create_task(self.auto_refresh())

    async def initialize_api(self):
        self.api = ConnectLifeApi(username="tudordanciu770@gmail.com", password=self.passwd)
        await self.api.login()

    async def select_device(self, nickname):
        await self.api.get_appliances()
        self.device = next((d for d in self.api.appliances if d.device_nickname == nickname and d.device_type == DeviceType.AIRCONDITIONER), None)

    async def refresh_status(self):
        try:
            await self.select_device(self.selected_device)
            if not self.device:
                return
            power = self.device.status_list.get("t_power")
            temp = self.device.status_list.get("t_temp")
            in_temp = self.device.status_list.get("f_temp_in")
            mode = self.device.status_list.get("t_work_mode")

            self.power_state = "ON" if str(power) == "1" else "OFF"
            self.target_temperature = str(temp) if temp is not None else "--"
            self.in_temperature = str(in_temp) if in_temp is not None else "--"

            mode_map = {"1": "Auto", "2": "Cool", "3": "Dry", "4": "Fan", "5": "Heat"}
            self.mode = mode_map.get(str(mode), "--")

            self.update_ui()
        except Exception as e:
            self.query_one("#status").update(f"[red]Error: {e}[/red]")

    async def auto_refresh(self):
        while True:
            await asyncio.sleep(5)
            if self.selected_device:
                await self.refresh_status()

    async def animate_status_bar(self):
        bar = self.query_one("#status-bar", Static)
        for i in range(0, 101, 5):
            bar.styles.width = f"{i}%"
            await asyncio.sleep(0.02)
        bar.styles.width = "0%"

    async def send_command(self, updates: dict):
        await self.animate_status_bar()
        await self.api.update_appliance(self.device.puid, updates)
        await asyncio.sleep(0.1)
        await self.refresh_status()

    def update_ui(self):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.query_one("#status").update(
            f"[b green]Power:[/b green] {self.power_state}    [b yellow]Target Temp:[/b yellow] {self.target_temperature}°C    [b cyan]In Temp:[/b cyan] {self.in_temperature}°C    [b magenta]Mode:[/b magenta] {self.mode}    [dim]Updated: {timestamp} | Device: {self.selected_device}[/dim]"
        )

    def update_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.query_one("#clock-display").update(f"[b]{now}[/b]")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Vertical(
            Horizontal(
                Static(r"""
    █████╗   ██████╗  ██████╗ ██████╗ ███████╗███████╗███████╗
   ██╔══██╗ ██╔════╝ ██╔════╝ ██╔══██╗██╔════╝██╔════╝██╔════╝
   ███████║ ██║  ███╗██║  ███╗██████╔╝█████╗  █████╗  ███████╗
   ██╔══██║ ██║   ██║██║   ██║██╔═══╝ ██╔══╝  ██╔══╝  ╚════██║
   ██║  ██║ ╚██████╔╝╚██████╔╝██║     ███████╗███████╗███████║
   ╚═╝  ╚═╝  ╚═════╝  ╚═════╝ ╚═╝     ╚══════╝╚══════╝╚══════╝
""", id="ascii-art"),
                Static("", id="clock-display")
            ),
            Static("[b]System Initializing...[/b]", id="status"),
            Static("", id="status-bar"),
            Horizontal(
                Select(options=[("AC1", "AC1"), ("AC2", "AC2")], id="device_select"),
                Button("Power ON", id="power_on", variant="success"),
                Button("Power OFF", id="power_off", variant="error")
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
                await self.send_command({"t_temp": new_temp})
            elif btn == "temp_down":
                temp_val = int(self.target_temperature) if self.target_temperature.isdigit() else 24
                new_temp = str(max(temp_val - 1, 16))
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
                    await self.send_command({"t_work_mode": mode_code, "t_power": "1"})
            elif btn == "fan_cycle":
                current_raw = str(self.device.status_list.get("t_fanspeedcv", "1"))
                current = int(current_raw) if current_raw.isdigit() else 1
                new_val = str(1 if current >= 6 else current + 1)
                await self.send_command({"t_fanspeedcv": new_val})
            elif btn == "swing_v":
                current = self.device.status_list.get("t_up_down", "0")
                new_state = "0" if str(current) == "1" else "1"
                await self.send_command({"t_up_down": new_state})
            elif btn == "swing_h":
                current = self.device.status_list.get("t_swing_direction", "0")
                new_state = "0" if str(current) == "1" else "1"
                await self.send_command({"t_swing_direction": new_state})
        except Exception as e:
            self.query_one("#status").update(f"[red]Error: {e}[/red]")

    async def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "device_select":
            self.selected_device = event.value
            await self.refresh_status()

if __name__ == "__main__":
    passwd = getpass("Enter password: ")
    AC1UI(passwd).run()
