from abc import ABC, abstractmethod
from datetime import date, timedelta
import random
import re
import json
import os

# ==== Absztrakt osztályok ====
class Auto(ABC):
    def __init__(self, rendszam, tipus, berleti_dij):
        self.rendszam = rendszam
        self.tipus = tipus
        self.berleti_dij = berleti_dij

    @abstractmethod
    def auto_info(self):
        pass

class Szemelyauto(Auto):
    def auto_info(self):
        return f"Személyautó - {self.tipus} ({self.rendszam})"

class Teherauto(Auto):
    def auto_info(self):
        return f"Teherautó - {self.tipus} ({self.rendszam})"

# ==== Bérlés osztály ====
class Berles:
    def __init__(self, auto, datum_tol, datum_ig):
        self.auto = auto
        self.datum_tol = datum_tol
        self.datum_ig = datum_ig

    def __str__(self):
        return f"{self.auto.auto_info()} - {self.datum_tol} - {self.datum_ig} - Ár: {self.napok_szama() * self.auto.berleti_dij} Ft"

    def napok_szama(self):
        return (self.datum_ig - self.datum_tol).days + 1

    def atfedi(self, masik_tol, masik_ig):
        return self.datum_tol <= masik_ig and self.datum_ig >= masik_tol

# ==== Autókölcsönző ====
class Autokolcsonzo:
    def __init__(self, nev):
        self.nev = nev
        self.autok = []
        self.berlesek = []

    def auto_berlese(self, rendszam, datum_tol, datum_ig):
        if not ellenoriz_rendszam(rendszam):
            return "Érvénytelen rendszám formátum. (Pl: ABC-123)"
        if datum_tol > datum_ig:
            return "Hibás dátumtartomány."

        for auto in self.autok:
            if auto.rendszam == rendszam:
                for berles in self.berlesek:
                    if berles.auto.rendszam == rendszam and berles.atfedi(datum_tol, datum_ig):
                        return "Ez az autó már ki van bérelve ezen időszakban."
                uj_berles = Berles(auto, datum_tol, datum_ig)
                self.berlesek.append(uj_berles)
                return f"Sikeres bérlés. Ár: {uj_berles.napok_szama() * auto.berleti_dij} Ft"
        return "Nincs ilyen rendszámú autó a rendszerben."

    def berles_lemondasa(self, rendszam, datum_tol, datum_ig):
        for berles in self.berlesek:
            if berles.auto.rendszam == rendszam and berles.datum_tol == datum_tol and berles.datum_ig == datum_ig:
                self.berlesek.remove(berles)
                return "A bérlés sikeresen le lett mondva."
        return "Nincs ilyen bérlés a rendszerben."

    def berlesek_listazasa(self):
        return [str(b) for b in self.berlesek]

    def szabad_autok(self, datum_tol, datum_ig):
        return [
            auto for auto in self.autok
            if all(not b.atfedi(datum_tol, datum_ig) or b.auto.rendszam != auto.rendszam for b in self.berlesek)
        ]

# ==== Segédfüggvények ====
def ellenoriz_rendszam(rsz):
    return re.match(r"^[A-Z]{3}-\d{3}$", rsz) is not None

def veletlen_rendszam():
    return f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))}-{random.randint(100,999)}"

def betolt_adat():
    kolcsonzo = Autokolcsonzo("Villám Rent")

    if os.path.exists("autok.json") and os.path.exists("berlesek.json"):
        with open("autok.json", "r") as f:
            autok_data = json.load(f)
            for auto in autok_data:
                if auto["tipus"] == "szemelyauto":
                    kolcsonzo.autok.append(Szemelyauto(auto["rendszam"], auto["nev"], auto["dij"]))
                else:
                    kolcsonzo.autok.append(Teherauto(auto["rendszam"], auto["nev"], auto["dij"]))

        with open("berlesek.json", "r") as f:
            berlesek_data = json.load(f)
            for b in berlesek_data:
                if "datum_tol" in b and "datum_ig" in b:
                    for auto in kolcsonzo.autok:
                        if auto.rendszam == b["rendszam"]:
                            kolcsonzo.berlesek.append(
                                Berles(auto, date.fromisoformat(b["datum_tol"]), date.fromisoformat(b["datum_ig"]))
                            )
    return kolcsonzo

def main():
    kolcsonzo = betolt_adat()

    while True:
        print("\n--- Autókölcsönző rendszer ---")
        print("1. Autó bérlése")
        print("2. Bérlés lemondása")
        print("3. Bérlések listázása")
        print("4. Kilépés")
        valasz = input("Válassz egy műveletet: ")

        if valasz == "1":
            try:
                datum_tol = date.fromisoformat(input("Bérlés kezdete (YYYY-MM-DD): "))
                datum_ig = date.fromisoformat(input("Bérlés vége (YYYY-MM-DD): "))

                if datum_tol > datum_ig:
                    print("Hibás időszak: a kezdő dátum nem lehet később, mint a záró dátum.")
                    continue

                elerhetok = kolcsonzo.szabad_autok(datum_tol, datum_ig)
                if not elerhetok:
                    print("Nincs elérhető autó ebben az időszakban.")
                    continue

                print("\n--- Elérhető autók ---")
                for i, auto in enumerate(elerhetok, 1):
                    print(f"{i}. {auto.auto_info()}")

                valasztott_index = int(input("Válassz egy autót (sorszám): ")) - 1
                if 0 <= valasztott_index < len(elerhetok):
                    auto = elerhetok[valasztott_index]
                    print(kolcsonzo.auto_berlese(auto.rendszam, datum_tol, datum_ig))
                else:
                    print("Érvénytelen sorszám.")

            except ValueError:
                print("Hibás dátumformátum. Használj YYYY-MM-DD formátumot.")

        elif valasz == "2":
            rendszam = input("Add meg a rendszámot (pl. ABC-123): ").strip().upper()
            datum_tol_input = input("Bérlés kezdete (YYYY-MM-DD): ")
            datum_ig_input = input("Bérlés vége (YYYY-MM-DD): ")
            try:
                datum_tol = date.fromisoformat(datum_tol_input)
                datum_ig = date.fromisoformat(datum_ig_input)
                print(kolcsonzo.berles_lemondasa(rendszam, datum_tol, datum_ig))
            except ValueError:
                print("Hibás dátumformátum.")

        elif valasz == "3":
            print("\n--- Aktuális bérlések ---")
            for b in kolcsonzo.berlesek_listazasa():
                print(b)

        elif valasz == "4":
            print("Kilépés... Adatok mentése folyamatban...")
            with open("berlesek.json", "w") as f:
                json.dump([
                    {"rendszam": b.auto.rendszam, "datum_tol": b.datum_tol.isoformat(), "datum_ig": b.datum_ig.isoformat()}
                    for b in kolcsonzo.berlesek
                ], f, indent=4)
            break

        else:
            print("Érvénytelen opció.")

if __name__ == "__main__":
    main()