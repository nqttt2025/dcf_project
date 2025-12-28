import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datatime import datetime
start_time =  datetime.now()
now = datetime.now()
st_string = now.strftime("%d/%m/%Y %H:%M:%S")



class DCF():
    def __init__(self) -> None:
        pass

    def preparing_DCF_ingredients(self):
        self.revenue_growth = None
        self.ebit_sales = None
        self.DA_sales = None
        self.Capex_sales = None
        self.delta_networking_capital = None
        self.tax_ebit = None
        self.Ebiat = None # Earing before interests after taxes
