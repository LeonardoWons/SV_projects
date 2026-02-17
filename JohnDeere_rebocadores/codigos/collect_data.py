from datetime import datetime
from collect_data_tugger import get_gps, get_status


# Function to generate random data / Função para gerar dados
def get_data():
    try:

        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current date and time / Data e hora atuais

        gps = get_gps()  # Fetch GPS data / Obter dados do GPS
        gps_latitude = gps[0]
        gps_longitude = gps[1]
        gps_altitude = gps[2]

        gps_signal_quality = gps[3]  # GPS signal quality / Qualidade do sinal GPS
        gps_satellite_count = gps[4]  # GPS satellite count / Quantidade de satélites GPS

        gps_pdop = gps[5]  # Positional dilution of precision (PDOP) / Diluição da precisão posicional (PDOP)
        gps_hdop = gps[6]  # Horizontal dilution of precision (HDOP) / Diluição da precisão horizontal (HDOP)
        gps_vdop = gps[7]  # Vertical dilution of precision (VDOP) / Diluição da precisão vertical (VDOP)

        gps_speed = gps[8]  # GPS speed / Velocidade GPS
        gps_direction = gps[9]  # GPS direction / Direção GPS

        b22 = get_status()  # Fetch tugger status / Obter status do rebocador
        tugger_status = b22[0]
        reverse_gear_status = b22[1]

        # Data dictionary to store all values / Dicionário de dados para armazenar todos os valores
        data = {
            "date_time": date_time,
            "gps_latitude": gps_latitude, "gps_longitude": gps_longitude, "gps_altitude": gps_altitude,
            "gps_signal_quality": gps_signal_quality, "gps_satellite_count": gps_satellite_count,
            "gps_pdop": gps_pdop, "gps_hdop": gps_hdop, "gps_vdop": gps_vdop,
            "gps_speed": gps_speed, "gps_direction": gps_direction,
            "tugger_status": tugger_status, "reverse_gear_status": reverse_gear_status,
            "current_value": 'not_get'  # 'not_collected' as default value / 'not_collected' como valor padrão
        }

        return data  # Return data dictionary / Retornar dicionário de dados

    except Exception as e:
        print(f"Error getting data: {e}")
        return ""
