import asyncio
from getpass import getpass
from connectlife.api import ConnectLifeApi
from connectlife.appliance import DeviceType
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, Header, Footer, LoadingIndicator, Select, DataTable, Input
from textual.reactive import reactive
from datetime import datetime, timedelta


class AC1UI(App):

    CSS = """
    Screen {
        background: #203a43;
        color: #e0e0e0;
        width: 100;
        height: 35;
        overflow: hidden;
    }
    Button {
        background: #2c3e50;
        color: #ecf0f1;
        padding: 0 2;
        height: 3;
        width: 20;
        max-width: 20;
        border: solid;
        text-style: bold;
    }
    Button:hover {
        background: #34495e;
        color: #1abc9c;
    }
    #power_on { background: #27ae60; color: black; }
    #power_off { background: #c0392b; color: black; }
    #ascii-art { color: #00bfff; text-style: bold underline; }
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
    .tiny-row Button { margin-right: 1; }
    #status-bar { height: 1; background: #1abc9c; width: 0%; transition: width 100ms; }
    #device_select { width: 12; max-width: 12; }
    Input, Select {
        width: 15;
        max-width: 15;
    }
    #schedule_list {
        height: 10;
        width: 100;
        max-width: 100;
        border: solid;
        background: #2c3e50;
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
        self.scheduled_actions = []
        self.last_power = "-"
        self.last_temp = "-"
        self.last_fan = "-"
        self.edit_index = None

    async def on_mount(self):
        await self.initialize_api()
        select = self.query_one("#device_select", Select)
        select.options = [("AC1", "AC1"), ("AC2", "AC2")]
        self.selected_device = "AC1"
        select.value = self.selected_device
        self.set_interval(1, self.update_clock)
        self.set_interval(1, self.check_schedules)
        self.polling_task = asyncio.create_task(self.auto_refresh())
        self.screen.styles.width = 100
        self.screen.styles.height = 35
        self.screen.styles.overflow = "hidden"

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

    def check_schedules(self):
        now = datetime.now()
        pending = [s for s in self.scheduled_actions if s["time"] <= now]
        for action in pending:
            if self.device:
                asyncio.create_task(self.send_command(action["command"]))
            self.scheduled_actions.remove(action)
        self.update_schedule_table()

    def schedule_action(self, delay_minutes, command_display, command_payload, replace_index=None):
        run_time = datetime.now() + timedelta(minutes=delay_minutes)
        new_action = {"time": run_time, "command_display": command_display, "command": command_payload}
        if replace_index is not None:
            self.scheduled_actions[replace_index] = new_action
        else:
            self.scheduled_actions.append(new_action)
        self.update_schedule_table()

    def update_schedule_table(self):
        table = self.query_one("#schedule_list", DataTable)
        table.clear(columns=True)
        table.add_columns("Time", "Power", "Temp", "Fan")
        for action in self.scheduled_actions:
            time_str = action["time"].strftime("%H:%M:%S")
            power = action["command_display"].get("Power", self.last_power)
            temp = action["command_display"].get("Temp", self.last_temp)
            fan = action["command_display"].get("Fan", self.last_fan)
            table.add_row(time_str, power, temp, fan)

    def compose(self) -> ComposeResult:
        yield Header()
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
                Button("Power ON", id="power_on"),
                Button("Power OFF", id="power_off")
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
            Horizontal(
                Input(placeholder="Hours", id="hours_input", value="0"),
                Input(placeholder="Minutes", id="minutes_input", value="0"),
                Select(options=[("Power ON", "1"), ("Power OFF", "0")], id="power_select"),
                Input(placeholder="Temp", id="temp_select"),
                Select(options=[("Fan Low", "2"), ("Fan Med", "4"), ("Fan High", "6")], id="fan_select"),
                Button("Add/Update", id="add_schedule"),
                Button("Edit", id="edit_schedule"),
                Button("Delete", id="delete_schedule")
            ),
            DataTable(id="schedule_list", show_header=True),
            Footer()
        )

    async def on_button_pressed(self, event: Button.Pressed):
        btn = event.button.id

        if btn in ["power_on", "power_off", "temp_up", "temp_down", "mode_cool", "mode_dry", "mode_fan", "mode_heat", "fan_cycle", "swing_v", "swing_h"]:
            await self.control_handler(btn)
        elif btn == "add_schedule":
            await self.handle_schedule()
        elif btn == "edit_schedule":
            self.edit_schedule()
        elif btn == "delete_schedule":
            self.delete_schedule()

    async def control_handler(self, btn):
        if btn == "power_on":
            await self.send_command({"t_power": "1"})
        elif btn == "power_off":
            await self.send_command({"t_power": "0"})
        elif btn in ["temp_up", "temp_down"]:
            temp_val = int(self.target_temperature) if self.target_temperature.isdigit() else 24
            new_temp = str(min(temp_val + 1, 30) if btn == "temp_up" else max(temp_val - 1, 16))
            await self.send_command({"t_temp": new_temp})
        elif btn.startswith("mode_"):
            mode_map = {"mode_cool": "2", "mode_dry": "3", "mode_fan": "4", "mode_heat": "5"}
            await self.send_command({"t_work_mode": mode_map.get(btn), "t_power": "1"})
        elif btn == "fan_cycle":
            current = int(self.device.status_list.get("t_fanspeedcv", "1"))
            new_val = str(1 if current >= 6 else current + 1)
            await self.send_command({"t_fanspeedcv": new_val})
        elif btn == "swing_v":
            new_val = "0" if self.device.status_list.get("t_up_down") == "1" else "1"
            await self.send_command({"t_up_down": new_val})
        elif btn == "swing_h":
            new_val = "0" if self.device.status_list.get("t_swing_direction") == "1" else "1"
            await self.send_command({"t_swing_direction": new_val})

    async def handle_schedule(self):
        h = float(self.query_one("#hours_input", Input).value or "0")
        m = float(self.query_one("#minutes_input", Input).value or "0")
        total_m = h * 60 + m
        power = self.query_one("#power_select", Select).value
        temp = self.query_one("#temp_select", Input).value
        fan = self.query_one("#fan_select", Select).value

        cmd_disp, cmd_payload = {}, {}

        if power:
            cmd_disp["Power"] = "ON" if power == "1" else "OFF"
            cmd_payload["t_power"] = power
            self.last_power = cmd_disp["Power"]

        if temp:
            cmd_disp["Temp"] = temp
            cmd_payload["t_temp"] = temp
            self.last_temp = temp

        if fan:
            cmd_disp["Fan"] = fan
            cmd_payload["t_fanspeedcv"] = fan
            self.last_fan = fan

        if cmd_payload:
            self.schedule_action(total_m, cmd_disp, cmd_payload, self.edit_index)
            self.edit_index = None

    def edit_schedule(self):
        t = self.query_one("#schedule_list", DataTable)
        if t.cursor_row is not None:
            s = self.scheduled_actions[t.cursor_row]
            mins = (s["time"] - datetime.now()).total_seconds() / 60
            self.query_one("#hours_input", Input).value = str(int(mins // 60))
            self.query_one("#minutes_input", Input).value = f"{mins % 60:.2f}"
            self.query_one("#power_select", Select).value = s["command"].get("t_power", "")
            self.query_one("#temp_select", Input).value = s["command"].get("t_temp", "")
            self.query_one("#fan_select", Select).value = s["command"].get("t_fanspeedcv", "")
            self.edit_index = t.cursor_row

    def delete_schedule(self):
        t = self.query_one("#schedule_list", DataTable)
        if t.cursor_row is not None:
            self.scheduled_actions.pop(t.cursor_row)
            self.update_schedule_table()


if __name__ == "__main__":
    passwd = getpass("Enter password: ")
    AC1UI(passwd).run()
