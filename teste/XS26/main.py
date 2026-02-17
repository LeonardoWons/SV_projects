from pymodbus.client import ModbusTcpClient

# Dados do dispositivo
ip = '192.168.0.128'  # Substitua pelo IP correto
porta = 502           # Porta padrão Modbus TCP

cliente = ModbusTcpClient(ip, port=porta)
cliente.connect()

# Ler registrador 40001 → índice 0
resposta = cliente.read_holding_registers(0, count=1)

if not resposta.isError():
    valor = resposta.registers[0]
    print(f"Registrador 40001 (VO1–VO16): valor bruto = {valor} ({bin(valor)})")

    for i in range(16):
        bit = (valor >> i) & 1
        print(f"VO{i+1:02} → {'ON' if bit else 'OFF'}")
else:
    print("Erro ao ler registrador.")

cliente.close()
