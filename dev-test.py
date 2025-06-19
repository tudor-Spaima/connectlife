import asyncio
from connectlife.api import ConnectLifeApi
from connectlife.appliance import DeviceType

async def main():
    api = ConnectLifeApi(username="tudordanciu770@gmail.com", password="Guravaii3!")
    await api.login()
    devices = await api.get_appliances()

    ac1 = next((d for d in devices if d.device_nickname == "AC1" and d.device_type == DeviceType.AIRCONDITIONER), None)
    if not ac1:
        print("AC1 not found.")
        return

    print(f"Found AC1 (PUID: {ac1.puid})")

    print("Current status:")
    for k, v in ac1.status_list.items():
        print(f"  {k}: {v}")

    # Final tested payload using true keys
    payload = {
        "t_power": 1
    }

    print("Sending command to turn off AC1...")
    await api.update_appliance(ac1.puid, payload)

    await asyncio.sleep(5)
    await api.get_appliances()
    ac1 = next((d for d in api.appliances if d.device_nickname == "AC1"), None)
    print("Updated t_power:", ac1.status_list.get("t_power"))

asyncio.run(main())
