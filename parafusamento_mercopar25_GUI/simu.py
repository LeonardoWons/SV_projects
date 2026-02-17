# -*- coding: utf-8 -*-
import time
import threading
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext, ModbusSequentialDataBlock
from pymodbus.server import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification

# =========================
# CONFIGURAÇÃO DO SERVIDOR
# =========================
PORTA = 5020  # use 5020 para evitar conflito com serviços do Windows/Linux
print(f"[SIMULADOR] Servidor rodando na porta {PORTA}")

# Endereços conforme o cliente espera
read_regs = {
    "circle1": 8,
    "circle2": 9,
    "circle3": 10,
    "circle4": 11,
    "fazendo_cruz": 12,
    "fazendo_tri": 13,
    "pronto": 14,
    "screw_error": 15,
}
write_regs = {
    "faz_cruz": 40,
    "faz_tri": 41,
}

# Inicializa todos os registradores como 0 (False)
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0] * 100),
    co=ModbusSequentialDataBlock(0, [0] * 100),
)
context = ModbusServerContext(slaves=store, single=True)


# =========================
# FUNÇÃO DE SIMULAÇÃO
# =========================
def robo_simulacao(context):
    """
    Simula o comportamento do robô:
    - Detecta quando o cliente escreve em faz_cruz ou faz_tri.
    - Simula processo de parafusamento.
    - Atualiza circle1..circleN e pronto.
    """
    while True:
        time.sleep(1)
        slave = context[0]
        # 1 = coils, 2 = discrete inputs (entrada)
        coils = slave.getValues(1, 0, 100)

        faz_cruz = bool(coils[write_regs["faz_cruz"]])
        faz_tri = bool(coils[write_regs["faz_tri"]])

        # Se o usuário pediu cruz
        if faz_cruz:
            print("[SIMULADOR] Iniciando sequência CRUZ")
            slave.setValues(2, read_regs["fazendo_cruz"], [1])
            for i in range(1, 5):
                time.sleep(2)
                print(f"  → Parafuso cruz{i} OK")
                slave.setValues(2, read_regs[f"circle{i}"], [1])
                time.sleep(2)
                slave.setValues(2, read_regs[f"circle{i}"], [0])

            time.sleep(3)

            slave.setValues(2, read_regs["fazendo_cruz"], [0])
            if not faz_tri:
                slave.setValues(2, read_regs["pronto"], [1])
                print("[SIMULADOR] CRUZ finalizado (pronto=True)")
                time.sleep(3)
                slave.setValues(2, read_regs["pronto"], [0])
            slave.setValues(1, write_regs["faz_cruz"], [0])

        time.sleep(3)

        # Se o usuário pediu triângulo
        if faz_tri:
            print("[SIMULADOR] Iniciando sequência TRIÂNGULO")
            slave.setValues(2, read_regs["fazendo_tri"], [1])
            for i in range(1, 4):
                time.sleep(1)
                print(f"  → Parafuso tri{i} OK")
                slave.setValues(2, read_regs[f"circle{i}"], [1])
                time.sleep(0.5)
                slave.setValues(2, read_regs[f"circle{i}"], [0])

            time.sleep(3)
            slave.setValues(2, read_regs["fazendo_tri"], [0])
            slave.setValues(2, read_regs["pronto"], [1])
            print("[SIMULADOR] TRIÂNGULO finalizado (pronto=True)")
            time.sleep(3)
            slave.setValues(2, read_regs["pronto"], [0])
            slave.setValues(1, write_regs["faz_tri"], [0])


# =========================
# IDENTIFICAÇÃO OPCIONAL
# =========================
identity = ModbusDeviceIdentification()
identity.VendorName = "SimuladorJaka"
identity.ProductCode = "RJ"
identity.VendorUrl = "http://example.com"
identity.ProductName = "Simulador do Robô"
identity.ModelName = "RoboFake"
identity.MajorMinorRevision = "1.0"


# =========================
# EXECUÇÃO DO SERVIDOR
# =========================
def start_simulador():
    t = threading.Thread(target=robo_simulacao, args=(context,), daemon=True)
    t.start()

    # 👇 Nova assinatura: apenas argumentos nomeados
    StartTcpServer(
        context=context,
        identity=identity,
        address=("0.0.0.0", PORTA)
    )

if __name__ == "__main__":
    start_simulador()