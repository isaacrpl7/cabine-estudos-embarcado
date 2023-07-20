import RPi.GPIO as GPIO
import time
from cabine import Cabine

print('Pressione Ctrl+C para sair')

cabine = Cabine(GPIO, 1)
# Loop principal
try:
    time_present = 0
    while True:
        cabine.loop()
        # Aguarda um tempo
        time.sleep(1)
 
except KeyboardInterrupt:
    # Ctrl+C foi pressionado
    cabine.print_lcd(u"Programa encerrado")
    cabine.set_light_status(0)
    GPIO.cleanup()  # Limpa configuração
    pass
 