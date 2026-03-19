import learn
import requests
import customtkinter as tk
from tkcalendar import Calendar
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from sklearn import linear_model
import numpy as np
from datetime import datetime, timedelta


class RadioButton(tk.CTkRadioButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)


class App(tk.CTk):

    def __init__(self):
        super().__init__()
        self.selected_currency = tk.StringVar(value="EUR")
        today = datetime.now()
        start_limit = today - timedelta(days=30)
        self.geometry("500x300")
        self.title("Kursy walut & predykcja")
        self.minsize(1450, 750)

        self.label = tk.CTkLabel(master=self, text="2. Wybierz walutę", width=120, height=25, fg_color="#57c1fa",
                                 corner_radius=8)
        self.label.grid(row=0, column=3)
        self.createRadioButtons()

        self.label12 = tk.CTkLabel(master=self, text="1. Wybierz datę początkową", width=120, height=25,
                                   fg_color="#57c1fa", corner_radius=8)
        self.label12.grid(row=0, column=0, padx=25, pady=10)
        self.cal = Calendar(self, selectmode='day', date_pattern='y-mm-dd')
        self.cal.selection_set(start_limit.date())
        self.cal.grid(row=1, column=0, columnspan=2, rowspan=5, padx=50)

        self.label2 = tk.CTkLabel(master=self, text="3. Wybierz datę końcową", width=120, height=25,
                                  fg_color=("#57c1fa"), corner_radius=8)
        self.label2.grid(row=0, column=4, padx=25)
        self.cal1 = Calendar(self, selectmode='day', date_pattern='y-mm-dd')
        self.cal1.selection_set(today.date())  # Ustawia kalendarz 2 na dzisiaj
        self.cal1.grid(row=1, column=4, padx=40, columnspan=2, rowspan=5)

        self.button = tk.CTkButton(master=self, text="Sprawdź kurs", command=self.getRates, width=120, height=100)
        self.button.grid(row=1, column=6, padx=20, pady=20, rowspan=5)

    def createRadioButtons(self):
        currency = ['EUR', 'USD', 'CHF', 'GBP', 'JPY']
        for i in range(len(currency)):
            radioButton = RadioButton(self, text=currency[i], variable=self.selected_currency, value=currency[i])
            radioButton.grid(row=i+1, column=3, sticky='ns')

    def display_info(self, rates, dates, start_col, title_prefix):

        currency = self.selected_currency.get()


        idx_max = np.argmax(rates)
        idx_min = np.argmin(rates)
        avg_val = np.mean(rates)

        # Nagłówek i zakres dat
        tk.CTkLabel(master=self, text=f"Liczba dni: {len(dates)}").grid(row=7, column=start_col, columnspan=3)

        tk.CTkLabel(master=self,
                    text=f"{title_prefix} {currency} od {dates[0]} do {dates[-1]}").grid(row=8, column=start_col, columnspan=3)


        tk.CTkLabel(master=self,
                    text=f"Wartość maksymalna {currency}: {rates[idx_max]:.2f} zł dnia: {dates[idx_max]}").grid(row=9, column=start_col, columnspan=3, padx=20)

        tk.CTkLabel(master=self,
                    text=f"Wartość minimalna {currency}: {rates[idx_min]:.2f} zł dnia: {dates[idx_min]}").grid(row=10, column=start_col, columnspan=3, padx=20)

        tk.CTkLabel(master=self,
                    text=f"Średnia wartość {currency}: {avg_val:.2f} zł").grid(row=11, column=start_col, columnspan=3, padx=20)



    def changeString(self, string):
        nstring = string.split('/')
        nstring1 = '20' + nstring[2] + '-' + (nstring[0] if len(nstring[0]) == 2 else '0' + nstring[0]) + '-' + (
            nstring[1] if len(nstring[1]) == 2 else '0' + nstring[1])
        return nstring1

    def plotGraph(self, rates, dates, row, column,title):
        fig = plt.figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(dates, rates, linewidth=5, label="Wartość kursu")
        ax.set_xlabel(' ')
        plt.title(title + self.selected_currency.get())

        num_ticks = 6
        xticks = np.linspace(0, len(dates) - 1, num_ticks, dtype=int)
        xticklabels = [dates[idx] for idx in xticks]
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels)

        average_rate = np.mean(rates)
        average_line = [average_rate] * len(rates)
        ax.plot(dates, average_line, color='red', linestyle='--', label='Średnia')

        ax.legend()  # Add legend

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().grid(row=row, column=column, columnspan=6,pady=50,padx=25)

    def getRates(self):
        try:
            # Pobieranie dat bezpośrednio z kalendarza
            start_date = self.cal.get_date()
            end_date = self.cal1.get_date()

            url = f"http://api.nbp.pl/api/exchangerates/rates/A/{self.selected_currency.get()}/{start_date}/{end_date}/"
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()['rates']
            dates = [item['effectiveDate'] for item in data]
            rates = [item['mid'] for item in data]

            self.plotGraph(rates, dates, 6, 0, 'Kurs historyczny: ')
            self.display_info(rates, dates, 0, "Kurs")
            self.prediction(rates, dates)
        except Exception as e:
            print(f"Błąd pobierania danych: {e}")

    def prediction(self, rates, dates):
        # 1. PRZYGOTOWANIE DANYCH HISTORYCZNYCH (Treningowych)
        # Tworzymy proste indeksy dni: 0, 1, 2... zamiast skomplikowanych dat numerycznych
        x_history = np.array(range(len(dates))).reshape(-1, 1)
        y_history = np.array(rates)

        # 2. NAUKA MODELU
        model = linear_model.LinearRegression()
        model.fit(x_history, y_history)  # Model uczy się trendu na podstawie historii

        # 3. PRZYGOTOWANIE PRZYSZŁOŚCI (Predykcja)
        # Chcemy przewidzieć np. kolejne 10 dni po ostatniej dacie w historii
        future_indices = np.array(range(len(dates), len(dates) + 10)).reshape(-1, 1)

        # Przewidujemy wartości dla tych nowych indeksów
        y_pred = model.predict(future_indices)

        # Tworzymy czytelne daty (Stringi) dla wykresu przyszłości
        last_day_dt = datetime.strptime(dates[-1], "%Y-%m-%d")
        string_dates = []
        for i in range(1, 11):
            next_day = last_day_dt + timedelta(days=i)
            string_dates.append(next_day.strftime("%Y-%m-%d"))

        # 4. WYŚWIETLENIE WYNIKÓW
        self.plotGraph(y_pred, string_dates, 6, 6, 'Przewidywany kurs ')
        self.display_info(y_pred, string_dates, 6, "Przewidywany kurs")

if __name__ == "__main__":
    app = App()
    app.mainloop()