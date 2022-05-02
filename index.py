from Application import *
import tkinter

root = tkinter.Tk()
root.title("Морской бой")
root.iconbitmap('./images/logo.ico')
root.geometry("900x600+100+100")

app = Application(master=root)
app.mainloop()
