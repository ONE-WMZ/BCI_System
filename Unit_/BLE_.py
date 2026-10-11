import asyncio
from bleak import BleakClient, BleakScanner


class BLE_:
    def __init__(self):
        self.client = None

    # ! Scan
    async def scan(self, timeout=3.0):
        print(f"Fcaning BLE device {timeout} s...")
        devices = await BleakScanner.discover(timeout=timeout)
        device_list = []
        for i, device in enumerate(devices):
            name = device.name
            address = device.address
            print(f"\t [{i + 1}] {name} \t: {address}")
            device_list.append((name, address))
        print(f"Scan OK, Find {len(devices)} device.")
        return device_list
    
    # ! Connect
    async def connect(self, device_name, timeout=4.0):
        if self.client and self.client.is_connected:
            await self.disconnect()
        try:
            print(f"Finding device: {device_name}")
            if ":" in device_name:
                device = await BleakScanner.find_device_by_address(device_name, timeout=timeout)
            else:
                device = await BleakScanner.find_device_by_name(device_name, timeout=timeout)
            if not device:
                print(f"【No find {device_name}】")
                return None
            self.client = BleakClient(device)
            await self.client.connect(timeout=timeout)
            if self.client.is_connected:
                print(f"Success Connnect: {device.name} ({device.address})")
                return self.client
            else:
                print("Connection failed, the client not in connected state.")
                self.client = None
                return None
        except Exception as e:
            print(f"【Error in connect: {e}】")
            self.client = None
            return None
        
    # ! Disconnect    
    async def disconnect(self):
        if self.client and self.client.is_connected:
            print(f"Disconnecting to {self.client.address} ...")
            await self.client.disconnect()
            self.client = None
            print("Disconnected.")
        else:
            print("No connections at the moment.")

    # ! Read Data
    async def read(self, char_uuid):
        if not self.client or not self.client.is_connected:
            print("【Error: Not connected to any device】")
            return None
        try:
            print(f"Reading from characteristic: {char_uuid}...")
            value = await self.client.read_gatt_char(char_uuid)
            print(f"Read Success: {value}")
            return value
        except Exception as e:
            print(f"【Error in read: {e}】")
            return None    
    
    # ! Write Data
    async def write(self, char_uuid, data):
        if not self.client or not self.client.is_connected:
            print("【Error: Not connected to any device】")
            return False
        try:
            print(f"Writing to characteristic: {char_uuid}...")
            await self.client.write_gatt_char(char_uuid, data, response=True)
            print("Write Success.")
            return True
        except Exception as e:
            print(f"【Error in write: {e}】")
            return False
        

# ! case
# async def main():
#     ble = BLE_()
#     await ble.scan(timeout=2.0)

# if __name__ == "__main__":
#     asyncio.run(main())