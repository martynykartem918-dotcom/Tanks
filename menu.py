import customtkinter as CTk

class Menu(CTk.CTk):
    def __init__(self):
        super().__init__()

        self.name = None
        self.host = None
        self.port = None
        self.title('Стрілялки Launcher')
        self.geometry('300x340')

        CTk.CTkLabel(self, text = 'ВХІД У ГРУ', font = ('Comic Sans MS', 25, 'bold')).pack(pady = 15, padx = 20, anchor = 'center')

        self.name_entry = CTk.CTkEntry(self, placeholder_text = 'Введіть ім`я 😊', height = 50, font = ('Comic Sans MS', 20))
        self.name_entry.pack(padx = 20, anchor = 'w', fill = 'x')

        self.host_entry = CTk.CTkEntry(self, placeholder_text = 'Введіть хост 😊', height = 50, font = ('Comic Sans MS', 20))
        self.host_entry.pack(padx = 20, pady = 15, anchor = 'w', fill = 'x')

        self.port_entry = CTk.CTkEntry(self, placeholder_text = 'Введіть порт сервера 😊', height = 50, font = ('Comic Sans MS', 20))
        self.port_entry.pack(padx = 20, anchor = 'w', fill = 'x')

        CTk.CTkButton(self, text = 'СТАРТ', command = self.open_game, height = 50, font = ('Comic Sans MS', 28, 'bold')).pack(pady = 15, padx = 20, fill = 'x')

    def open_game(self):
        self.name = self.name_entry.get()
        self.host = self.host_entry.get()
        self.port = int(self.port_entry.get())
        self.destroy()
