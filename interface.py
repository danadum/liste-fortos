import os
import sys
from threading import Thread
from tkinter import *
from tkinter.filedialog import askdirectory
import xml.etree.ElementTree as Tree
from tkinter.messagebox import showinfo, showerror, showwarning

import requests
from my_socket import MySocket
import json


class Interface(Tk):
    def __init__(self):
        super().__init__()
        self.nom = StringVar()
        self.mdp = StringVar()
        self.royaume = StringVar()
        self.serveur = StringVar()
        self.dossier = StringVar()
        self.fichier = StringVar()
        self.intervalle = IntVar()
        self.serveurs = {}
        self.royaumes = {"Glaces": 2, "Sables": 1, "Pics": 3}
        self.remember = BooleanVar()
        self.socket = None
        self.scan_state = StringVar()

        self.get_serveurs()
        if os.path.exists("config.json"):
            with open("config.json") as file:
                data = json.load(file)
                self.nom.set(data.get("nom") or "")
                self.mdp.set(data.get("mdp") or "")
                self.serveur.set(data.get("serveur") or "France 1")
                self.royaume.set(data.get("royaume") or "Glaces")
                self.dossier.set(data.get("dossier") or "")
                self.fichier.set(data.get("fichier") or "forteresses.xlsx")
                self.intervalle.set(data.get("intervalle") or 10)
        else:
            self.serveur.set("France 1")
            self.royaume.set("Glaces")
            self.fichier.set("forteresses.xlsx")
            self.intervalle.set(10)

        self.minsize(400, 400)
        self.protocol("WM_DELETE_WINDOW", self.close)

        content = Frame()
        content.place(relx=.5, rely=.5, anchor="center")
        Label(content, text="Nom d'utilisateur :").grid(row=0, column=0, sticky="W", pady=5)
        Entry(content, textvariable=self.nom).grid(row=0, column=1)
        Label(content, text="Mot de passe :").grid(row=1, column=0, sticky="W", pady=5)
        Entry(content, textvariable=self.mdp).grid(row=1, column=1)
        Label(content, text="Serveur :").grid(row=2, column=0, sticky="W", pady=5)
        OptionMenu(content, self.serveur, *self.serveurs).grid(row=2, column=1)
        Label(content, text="Royaume :").grid(row=3, column=0, sticky="W", pady=5)
        OptionMenu(content, self.royaume, *self.royaumes).grid(row=3, column=1)
        Label(content, text="Dossier :").grid(row=4, column=0, sticky="W", pady=5)
        Entry(content, textvariable=self.dossier).grid(row=4, column=1)
        Button(content, text='Choisir', command=self.get_dossier).grid(row=4, column=2)
        Label(content, text="Nom du fichier :").grid(row=5, column=0, sticky="W", pady=5)
        Entry(content, textvariable=self.fichier).grid(row=5, column=1, padx=5)
        Label(content, text="Temps entre 2 scans (min) :").grid(row=6, column=0, sticky="W", pady=5)
        Scale(content, variable=self.intervalle, from_=2, to=60, orient=HORIZONTAL).grid(row=6, column=1, columnspan=2,
                                                                                         padx=5)
        Checkbutton(content, text='Enregistrer les informations', variable=self.remember).grid(row=7, columnspan=2,
                                                                                               sticky="W", pady=5)
        self.button_run = Button(content, text='Run', command=self.start_socket)
        self.button_run.grid(row=8, column=0)
        self.button_stop = Button(content, text='Stop', command=self.stop_socket, state=DISABLED)
        self.button_stop.grid(row=8, column=1)
        Label(content, textvariable=self.scan_state).grid(row=9, column=0, columnspan=2)

    def start_socket(self):
        if self.nom.get() != "" and self.mdp.get() != "" and self.fichier.get() != "":
            if os.path.exists(self.dossier.get()):
                if not self.fichier.get().endswith(".xlsx"):
                    self.fichier.set(self.fichier.get() + ".xlsx")
                self.socket = MySocket(self,
                                       self.serveurs[self.serveur.get()]["url"],
                                       self.serveurs[self.serveur.get()]["header"],
                                       self.royaumes[self.royaume.get()],
                                       self.nom.get(),
                                       self.mdp.get(),
                                       f"{self.dossier.get()}/{self.fichier.get()}",
                                       self.intervalle.get())
                Thread(target=self.socket.run_forever, kwargs={'reconnect': 5}, daemon=True).start()
                self.button_run["state"] = DISABLED
                self.button_stop["state"] = NORMAL
                if self.remember.get():
                    with open('config.json', 'w') as file:
                        json.dump({
                            "nom": self.nom.get(),
                            "mdp": self.mdp.get(),
                            "royaume": self.royaume.get(),
                            "serveur": self.serveur.get(),
                            "dossier": self.dossier.get(),
                            "fichier": self.fichier.get(),
                            "intervalle": self.intervalle.get()
                        }, file)
            else:
                showwarning("Attention", "Le chemin du dossier est invalide !")
        else:
            showwarning("Attention", "Tous les champs doivent être remplis !")

    def stop_socket(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None
        self.scan_state.set("")
        self.button_run["state"] = NORMAL
        self.button_stop["state"] = DISABLED

    def get_serveurs(self):
        text = requests.get("https://langserv.public.ggs-ep.com/em/fr").json()
        root = Tree.fromstring(requests.get("https://empire-html5.goodgamestudios.com/config/network/1.xml").text)
        for instance in root[0]:
            self.serveurs[f"{text.get(instance[6].text)} {instance[4].text}"] = {
                "url": f"wss://{instance[0].text}",
                "header": instance[2].text
            }

    def get_dossier(self):
        self.dossier.set(askdirectory(initialdir='~'))
        if self.dossier.get() == "":
            showinfo("Attention", "Aucun dossier sélectionné !")

    def show_error(self, error):
        showerror("Erreur", error)
        self.button_run["state"] = NORMAL
        self.button_stop["state"] = DISABLED
        self.socket = None
        self.scan_state.set("")

    def close(self):
        self.stop_socket()
        self.destroy()
        sys.exit(0)
