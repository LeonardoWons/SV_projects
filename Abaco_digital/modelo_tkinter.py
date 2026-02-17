import tkinter
import threading
import asyncio
from tkinter import ttk

tela = tkinter.Tk()


async def tkinter_tela():
    global tela

    frm = ttk.Frame(tela, padding=100)
    frm.grid()
    ttk.Label(frm, text="teste").grid(column=0, row=0)
    tela.mainloop()


gui = threading.Thread(target=asyncio.run(tkinter_tela()), daemon=True)
gui.start()
gui.join()
