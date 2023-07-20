from enum import Enum
from caller import Caller
from RPLCD import CharLCD
import re


# Tempos em segundos
MAX_WAITING_TIME = 20
FREQUENCIA_CHECAGEM_RESERVA = 10
MAX_RESERVE_WAITING_TIME = 15 # Quanto tempo até a cabine entender que alguém foi ao banheiro
MAX_RESERVE_TOLERANCE_TIME = 30 # Quanto tempo até a cabine ficar livre

class Status(Enum):
    FREE = 0
    RESERVED = 1
    OCCUPIED = 2

class Cabine:

    def __init__(self, gpio, id) -> None:
        self.status = Status.FREE
        self.id = id

        self.lightPin = 11
        self.sensorPin = 13

        gpio.setmode(gpio.BOARD)       # Pinagem física
        gpio.setup(self.lightPin, gpio.OUT)   # Pino de led como saída
        gpio.setup(self.sensorPin, gpio.IN)    # Pino do sensor como entrada e aciona o pull-up
        gpio.output(self.lightPin, gpio.HIGH) # Desliga o led

        self.lcd = CharLCD(cols=16, rows=2, pin_rs=37, pin_e=35, pins_data=[40, 38, 36, 32, 33, 31, 29, 23], numbering_mode=gpio.BOARD)
        self.lcd.write_string(u"Iniciando programa")
        self.gpio = gpio
        self.caller = Caller()
        
        self.is_in_reserve = False
        self.waiting_time = 0
        self.clock = 0
        self.reserve_waiting_time = 0
        self.print_lcd(u'Cabine disponivel...')

    def loop(self):
        if self.clock > FREQUENCIA_CHECAGEM_RESERVA:
            self.checar_reserva()
            self.clock = 0
        
        if not self.is_in_reserve:
            self.handle_presenca()
        else:
            self.handle_reservated()

        self.clock += 1

    def checar_reserva(self):
        print("Checando reserva...")
        self.print_lcd(u'checando reserva...')
        availability = self.caller.check_availability(self.id)
        next_reservation = self.caller.get_next_reservation(self.id)
        
        if availability.get('end_time'):
            if not self.is_in_reserve:
                self.status = Status.RESERVED
                self.is_in_reserve = True
            hour = re.sub(r'^.*?T', "", availability.get('end_time'))
            self.print_lcd(f"Reserva ate     {hour}")

        if next_reservation.get('horario', None) and not availability.get('end_time'):
            self.print_lcd(f"Prox:{next_reservation.get('horario', None)}")
            self.is_in_reserve = False
        if not next_reservation.get('horario', None) and not availability.get('end_time'):
            self.print_lcd(u'Sem reservas feitas')
            self.is_in_reserve = False

    def handle_presenca(self):
        # Cabine livre e sensor identificou movimento
        if self.status == Status.FREE and self.get_sensor_status() == self.gpio.HIGH:
            self.status = Status.OCCUPIED
            self.waiting_time = MAX_WAITING_TIME
            self.set_light_status(self.gpio.LOW)
            print("Acender luz")
            self.caller.set_availability(self.id, 'OCUPADA')
        
        # Cabine ocupada e o sensor identifica movimento
        if self.status == Status.OCCUPIED and self.get_sensor_status() == self.gpio.HIGH:
            self.waiting_time = MAX_WAITING_TIME
        
        # Cabine ocupada e sensor não identifica mais movimento
        if self.status == Status.OCCUPIED and self.get_sensor_status() == self.gpio.LOW:
            self.waiting_time -= 1
        
        # Cabine ocupada e o tempo de espera terminou
        if self.status == Status.OCCUPIED and self.waiting_time <= 0:
            self.status = Status.FREE
            self.waiting_time = 0
            self.set_light_status(self.gpio.HIGH)
            print("Apagar luz")
            self.caller.set_availability(self.id, 'DISPONIVEL')
            
        print(f"Tempo de espera: {self.waiting_time}s")
    
    def handle_reservated(self):
        if self.status == Status.RESERVED and self.get_sensor_status() == self.gpio.HIGH:
            self.reserve_waiting_time = 0
            print(self.caller.set_availability(self.id, "OCUPADA"))
            self.status = Status.OCCUPIED

        if self.get_sensor_status() == self.gpio.LOW:
            self.reserve_waiting_time += 1
        
        if self.get_sensor_status() == self.gpio.HIGH:
            self.reserve_waiting_time = 0
        
        if self.status == Status.OCCUPIED and self.reserve_waiting_time > MAX_RESERVE_WAITING_TIME:
            # Remover a reserva e coloca status da cabine como livre e apaga a lâmpada
            print(self.caller.set_availability(self.id, "RESERVADA"))
            self.status = Status.RESERVED
        
        if self.reserve_waiting_time > MAX_RESERVE_TOLERANCE_TIME:
            self.caller.set_availability(self.id, "DISPONIVEL")
            self.status = Status.FREE
            self.caller.cancel_current_reservation(self.id)
            self.is_in_reserve = False

        # Checar status
        if self.status == Status.RESERVED or self.status == Status.OCCUPIED:
            self.set_light_status(self.gpio.LOW)
        elif self.status == Status.FREE:
            self.set_light_status(self.gpio.HIGH)
        
        print(f"Tempo de espera (reservado): {self.reserve_waiting_time}s")

    def print_lcd(self, phrase: str):
        self.lcd.clear()
        self.lcd.write_string(f"{phrase}")

    def set_light_status(self, status):
        self.gpio.output(self.lightPin, status)

    def get_sensor_status(self):
        return self.gpio.input(self.sensorPin)