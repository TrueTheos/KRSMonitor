import requests
import json
from fp.fp import FreeProxy
import threading

provinceNames = [
"KUJAWSKO-POMORSKIE",
"LUBELSKIE",
"LUBUSKIE",
"ŁÓDZKIE",
"MAŁOPOLSKIE",
"MAZOWIECKIE",
"OPOLSKIE",
"PODKARPACKIE",
"PODLASKIE",
"POMORSKIE",
"ŚLĄSKIE",
"ŚWIĘTOKRZYSKIE",
"WARMIŃSKO-MAZURSKIE",
"WIELKOPOLSKIE",
"ZACHODNIOPOMORSKIE",
"DOLNOŚLĄSKIE"
]

provinces = {}

headers = {
    "Content-Type": "application/json",
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
}

url = "https://prs-openapi2-prs-prod.apps.ocp.prod.ms.gov.pl/api/wyszukiwarka/krs"

class Business:
    def __init__(self, name, number, city) -> None:
        self.name = name
        self.number = number
        self.city = city

    def to_dict(self):
        return {
            'name': self.name,
            'number': self.number,
            'city': self.city
        }

class Province:
    def __init__(self, name) -> None:
        self.name = name
        self.businesses = []

    def parseResponse(self, response):
        self.businesses.extend([Business(business['nazwa'], business['numer'], business['miejscowosc']) for business in response['listaPodmiotow']])

    def to_dict(self):
        return {
            'name': self.name,
            'businesses': [business.to_dict() for business in self.businesses]
        }    

def processPage(province: Province, page, url, headers, payload):
    proxy = FreeProxy(rand=True, https=True).get()
    proxies = {'https': proxy}
    print("Processing page", page)
    payload["paginacja"]["numerStrony"] = page
    response = requests.post(url, headers=headers, data=json.dumps(payload), proxies=proxies)
    jsonResponse = response.json()
    province.parseResponse(jsonResponse)

def getProvinceInfo(province: Province):
    print(province.name)

    payload = {
        "rejestr": ["P", "S"],
        "podmiot": {
            "krs": None,
            "nip": None,
            "regon": None,
            "nazwa": None,
            "wojewodztwo": province.name,
            "powiat": "",
            "gmina": "",
            "miejscowosc": ""
        },
        "status": {
            "czyOpp": None,
            "czyWpisDotyczacyPostepowaniaUpadlosciowego": None,
            "dataPrzyznaniaStatutuOppOd": None,
            "dataPrzyznaniaStatutuOppDo": None
        },
        "paginacja": {
            "liczbaElementowNaStronie": 1000,
            "maksymalnaLiczbaWynikow": 1000,
            "numerStrony": 1
        }
    } 

    proxies = {
        'https': '',
    }

    proxy = FreeProxy(rand=True, https=True).get()
    proxies['https'] = proxy

    response = requests.post(url, headers=headers, data=json.dumps(payload), proxies=proxies)
    jsonResponse = response.json()

    province.parseResponse(jsonResponse)

    count = int(jsonResponse["liczbaPodmiotow"])

    threads = []

    for page in range(2, count // 1000):
        thread = threading.Thread(target=processPage, args=(province, page, url, headers, payload))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    print(province.name + " " + str(count))
    

if __name__ == "__main__":
    provinces = {string: Province(string) for string in provinceNames}

    for key, value in provinces.items():
        getProvinceInfo(value)
        jsonDump = json.dumps(value.to_dict(), indent=4)
        with open(f"{key}.json", "w") as outfile:
            outfile.write(jsonDump)
    