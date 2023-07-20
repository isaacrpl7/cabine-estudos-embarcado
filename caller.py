import requests
import json


# The API endpoint
URL = "https://rare-cow-9.telebit.io/"

class Caller:

    def __init__(self):
        self.url = URL
    
    def check_availability(self, id_cabine):
        # Make the get request
        response = requests.get(f"{self.url}cabines/{id_cabine}")

        # Get the response
        obj = response.json()
        return {"status": obj.get('status'), "start_time": obj.get('horarioInicial'), "end_time": obj.get('horarioFinal')}

    def get_next_reservation(self, id_cabine):
        response = requests.get(f"{self.url}cabines/{id_cabine}/proxima-reserva")
        obj = response.json()
        return {"horario": obj.get('horario'), "usuario": obj.get('usuario')}
    
    def cancel_current_reservation(self, id_cabine):
        response = requests.put(f"{self.url}cabines/{id_cabine}/cancelar")

        return response.status_code

    def set_availability(self, id_cabine, availability):
        data = {
            "status": availability
        }
        headers={
            'Content-type':'application/json',
            'Accept':'application/json'
        }
        data = json.dumps(data)
        print(data)
        # print(f"{self.url}cabines/{id_cabine}/status")
        
        response = requests.put(f"{self.url}cabines/{id_cabine}/status", data=data, headers=headers)

        return response.status_code