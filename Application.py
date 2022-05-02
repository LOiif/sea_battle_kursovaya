import math
from random import randrange
import time
from tkinter import *
from Ship import *
from tkinter.messagebox import *
from threading import Thread
from playsound import playsound
import configparser
import atexit

class Application(Frame):
    '''
    Приложение. Наследует класс Frame. Создание окна, холста и всех функций для реализации приложения
    '''
    
    width = 800 # ширина рабочего поля
    height = 400 # высота рабочего поля
    bg = "white" # цвет фона холста

    indent = 2 # отступ между ячейками
    gauge = 32  # размер одной из сторон квадратной ячейки

    whose_move = 'user' # чей сейчас ход
    is_game_start = False # началась ли игра
    develop_mode = False # режим для упрощения отладки

    offset_y = 40  # смещение по y (отступ сверху)
    offset_x_user = 30   # смещение по x пользовательского поля
    offset_x_comp = 430  # смещение по x поля компьютера

    fleet_time = 0  # время генерации флота
    fleet_comp = [] # флот компа
    fleet_user = [] # флот пользователя

    user_shoots = [] # массив точек, в которые стрелял пользователь
    comp_shoots = [] # массив точек, в которые стрелял компьютер
    comp_hits = {} # словарь попадний компьютера, где ключ - позиция корабля в массиве корбалей, а значение - массив попаданий

    comp_delay = 0.2 if develop_mode == True else 0.7 # задержка компьютера перед выстрелом (чтобы он не стрелял, как из автомата)
      
    ###################################################
    ###########  уровень сложности  ###################
    ###################################################
    # при уровне 'easy' компьютер будет стрелять рандомно
    # при уровне 'medium' компьютер смотрит, куда он стрелял в предыдущий раз (дальше одного, предыдущего хода он не помнит)
    # при уровне 'hard' компьютер помнит свои все попадания и на основе этого делает свой ход 
    comp_level = 'easy'

    #добавление холста на окно
    def createCanvas(self):
        try:
            self.canv.destroy()
        except AttributeError:
            print(AttributeError)

        self.canv = Canvas(self)
        self.canv["height"] = self.height
        self.canv["width"] = self.width
        self.canv["bg"] = self.bg
        self.canv.pack()
        self.canv.bind("<Button-1>",self.userPlay)

    def new_game(self):
        self.createCanvas()
        self.is_game_start = True
        self.renderGameStartButton()
        self.canv.delete('all')
        self.comp_shoots = []
        self.user_shoots = []
        self.comp_hits = {}
        self.whose_move = 'user'
        
        #добавление игровых полей пользователя и компьютера
        #создание поля для пользователя

        #перебор строк
        for i in range(10):
            #перебор столбцов
            for j in range(10):
                xn = j*self.gauge + (j+1)*self.indent + self.offset_x_user
                xk = xn + self.gauge
                yn = i*self.gauge + (i+1)*self.indent + self.offset_y
                yk = yn + self.gauge
                #добавление прямоугольника на холст с тегом в формате:
                #префикс_строка_столбец
                self.canv.create_rectangle(xn,yn,xk,yk,tag = "my_"+str(i)+"_"+str(j))

        #создание поля для компьютера
        #перебор строк
        for i in range(10):
            #перебор столбцов
            for j in range(10):
                xn = j*self.gauge + (j+1)*self.indent + self.offset_x_comp
                xk = xn + self.gauge
                yn = i*self.gauge + (i+1)*self.indent + self.offset_y
                yk = yn + self.gauge
                #добавление прямоугольника на холст с тегом в формате:
                #префикс_строка_столбец
                self.canv.create_rectangle(xn,yn,xk,yk,tag = "nmy_"+str(i)+"_"+str(j),fill="white")

        #добавление букв и цифр
        for i in reversed(range(10)):
            #цифры пользователя
            xc = self.offset_x_user - 15
            yc = i*self.gauge + (i+1)*self.indent + self.offset_y + round(self.gauge/2)
            self.canv.create_text(xc,yc,text=str(i+1))
            #цифры компьютера
            xc = self.offset_x_comp - 15
            yc = i*self.gauge + (i+1)*self.indent + self.offset_y + round(self.gauge/2)
            self.canv.create_text(xc,yc,text=str(i+1))
        #буквы
        symbols = "АБВГДЕЖЗИК"
        for i in range(10):
            #буквы пользователя
            xc = i*self.gauge + (i+1)*self.indent + self.offset_x_user + round(self.gauge/2)
            yc = self.offset_y - 15
            self.canv.create_text(xc,yc,text=symbols[i])

            #буквы компьютера
            xc = i*self.gauge + (i+1)*self.indent + self.offset_x_comp + round(self.gauge/2)
            yc = self.offset_y - 15
            self.canv.create_text(xc,yc,text=symbols[i])

        self.fleet_time = time.time()

        Thread(target=self.createShips, args=("nmy",)).start() #генерация кораблей противника
        # self.createShips("nmy")
        self.createShips("my") #генерация своих кораблей  

    def createShips(self, prefix):
        #функция генерации кораблей на поле
        #количество сгенерированных кораблей
        count_ships = 0
        while count_ships < 10:
            fleet_array = [] # массив занятых кораблями точек
            count_ships = 0 # обнулить количество кораблей
            fleet_ships = [] # массив с флотом

            #генерация кораблей (length - палубность корабля)
            for length in reversed(range(1,5)):
                #генерация необходимого количества кораблей необходимой длины
                for i in range(5-length):
                    #генерация точки со случайными координатами, пока туда не установится корабль
                    try_create_ship = 0
                    while 1:
                        try_create_ship += 1
                        
                        if try_create_ship > 50: # если количество попыток превысило 50, начать всё заново
                            break
                      
                        ship_point = prefix+"_"+str(randrange(10))+"_"+str(randrange(10)) # генерация точки со случайными координатами
                        orientation = randrange(2) # случайное расположение корабля (либо горизонтальное, либо вертикальное)
                        new_ship = Ship(length,orientation,ship_point) # создать экземпляр класса Ship 

                        #если корабль может быть поставлен корректно и его точки не пересекаются с уже занятыми точками поля
                        #пересечение множества занятых точек поля и точек корабля:
                        intersect_array = list(set(fleet_array) & set(new_ship.around_map+new_ship.coord_map))
                        if new_ship.ship_correct == 1 and len(intersect_array) == 0:
                            #добавить в массив со всеми занятыми точками точки вокруг корабля и точки самого корабля
                            fleet_array += new_ship.around_map + new_ship.coord_map
                            fleet_ships.append(new_ship)
                            count_ships += 1
                            break
        print(prefix,time.time() - self.fleet_time,"секунд")
        #отрисовка кораблей
        if prefix == "nmy":
            self.fleet_comp = fleet_ships
            self.paintShips(fleet_ships, prefix)
        else:
            self.fleet_user = fleet_ships
            self.paintShips(fleet_ships, prefix)

    #метод для отрисовки кораблей
    def paintShips(self,fleet_ships, prefix):
        if prefix == "nmy":
            fill = "lightgray" if self.develop_mode else "white"
            for obj in fleet_ships:
                for point in obj.coord_map:
                    self.canv.itemconfig(point,fill=fill)
        else:
            for obj in fleet_ships:
                for point in obj.coord_map:
                    self.canv.itemconfig(point,fill="gray")

    #метод рисования в ячейке креста на белом фоне
    def paintCross(self,xn,yn,tag):
        xk = xn + self.gauge
        yk = yn + self.gauge
        self.canv.itemconfig(tag,fill="#e6dada")
        self.canv.create_line(xn+4,yn+4,xk-4,yk-4,width="2",fill='red')
        self.canv.create_line(xk-4,yn+4,xn+4,yk-4,width="2",fill='red')

    #метод рисования промаха
    def paintMiss(self,point):
        #найти координаты
        new_str = int(point.split("_")[1])
        new_stlb = int(point.split("_")[2])
        if point.split("_")[0] == "nmy":
            xn = new_stlb*self.gauge + (new_stlb+1)*self.indent + self.offset_x_comp
        else:
            xn = new_stlb*self.gauge + (new_stlb+1)*self.indent + self.offset_x_user
        yn = new_str*self.gauge + (new_str+1)*self.indent + self.offset_y
        #добавить прямоугольник
        self.canv.itemconfig(point,fill="#d4d3e3")
        self.canv.create_oval(xn+12,yn+12,xn+18,yn+18,fill="#6157ff")

    #метод проверки финиша
    def checkFinish(self,type):
        '''type - указание, от чьего имени идёт обращение'''
        status = 0
        if type == "user":
            for ship in self.fleet_comp:
                status += ship.death
        else:
            for ship in self.fleet_user:
                status += ship.death
        return status
    
    #метод для генерации функции подсета баллов на основе переданной оси
    def generateCheckOppositeAxis (self, axis):
        if axis == 'X':
            def f(i, j):
                o = 0
                if (i-1 >= 0 and not("my_"+str(i-1)+"_"+str(j) in self.comp_shoots)) or i-1 < 0:
                    o += 1
                    if (i-2 >= 0 and not("my_"+str(i-2)+"_"+str(j) in self.comp_shoots)) or i-2 < 0:
                        o += 1
                    
                if (i+1 <= 9 and not("my_"+str(i+1)+"_"+str(j) in self.comp_shoots)) or i+1 > 9:
                    o += 1
                    if (i+2 <= 9 and not("my_"+str(i+2)+"_"+str(j) in self.comp_shoots)) or i+2 > 9:
                        o += 1
                return o
          
        elif axis == 'Y':
            def f(i, j):
                o = 0
                if (j-1 >= 0 and not("my_"+str(i)+"_"+str(j-1) in self.comp_shoots)) or j-1 < 0:
                    o += 1
                    if (j-2 >= 0 and not("my_"+str(i)+"_"+str(j-2) in self.comp_shoots)) or j-2 < 0:
                        o += 1
                    
                if (j+1 <= 9 and not("my_"+str(i)+"_"+str(j+1) in self.comp_shoots)) or j+1 > 9:
                    o += 1
                    if (j+2 <= 9 and not("my_"+str(i)+"_"+str(j+2) in self.comp_shoots)) or j+2 > 9:
                        o += 1
                return o
    
        return f

    #метод игры компьютера
    def compPlay(self,step = 0):
        time.sleep(self.comp_delay) # симуляция задержки компьютера
    
        if(self.comp_level == 'easy'):

            # на легком уровне сложности будем стрелять в случайно выбранные клетки
            while 1:
                    i = randrange(10)
                    j = randrange(10)
                    if not("my_"+str(i)+"_"+str(j) in self.comp_shoots):
                        break

            xn = j*self.gauge + (j+1)*self.indent + self.offset_x_user
            yn = i*self.gauge + (i+1)*self.indent + self.offset_y
            hit_status = 0
            n = 0
            for obj in self.fleet_user:
                n += 1
                #если координаты точки совпадают с координатой корабля, то вызвать метод выстрела
                if "my_"+str(i)+"_"+str(j) in obj.coord_map:

                    hit_status = 1 #изменить статус попадания
                    self.paintCross(xn,yn,"my_"+str(i)+"_"+str(j)) #мы попали, поэтому надо нарисовать крест
                    playsound("./sounds/vzryv.wav", block=False) #включаем звук попадания
                    self.comp_shoots.append("my_"+str(i)+"_"+str(j)) #добавить точку в список выстрелов компьютера
                
                    # если точки нет в словаре попаданий, добавляем (сделано для поддержки динамического переключения уровня сложности во время игры)
                    # в качестве ключа выступает позиция корабля в массиве кораблей пользователя
                    # в качестве значения - массив попаданий в корабль с индексом n
                    if not(n in self.comp_hits):
                        self.comp_hits[n] = []

                    self.comp_hits[n].append("my_"+str(i)+"_"+str(j))

                    #если метод вернул двойку, значит, корабль убит
                    if obj.shoot("my_"+str(i)+"_"+str(j)) == 2:
                        hit_status = 2
                        #изменить статус корабля
                        obj.death = 1
                        self.comp_hits.pop(n)
                        #все точки вокруг корабля сделать точками, в которые мы уже стреляли
                        for point in obj.around_map:
                            
                            self.paintMiss(point) #нарисовать промахи
                            self.comp_shoots.append(point)  #добавить точки вокруг корабля в список выстрелов компьютера
                    break
            #если статус попадания остался равным нулю - значит, мы промахнулись, передать управление компьютеру
            #иначе дать пользователю стрелять
            print("hit_status",hit_status)
            if hit_status == 0:
                #добавить точку в список выстрелов
                self.comp_shoots.append("my_"+str(i)+"_"+str(j))
                self.paintMiss("my_"+str(i)+"_"+str(j))
                #включаем звук промоха
                playsound("./sounds/vsplesk.wav", block=False)
                #ход переходит к пользователю
                self.whose_move = "user"
            else:
                #проверить выигрыш, если его нет - передать управление компьютеру
                if self.checkFinish("comp") < 10:
                    if hit_status == 1:
                        step += 1
                        if step > 4:
                            Thread(target=self.compPlay, args=(0,)).start()
                        else:
                            Thread(target=self.compPlay, args=(step,)).start()
                    else:
                        Thread(target=self.compPlay, args=(0,)).start()
                else:
                    showinfo("Морской бой", "Вы проиграли!")
        
        if(self.comp_level == 'hard'):

            # если в словаре попаданий ничего нет (мы либо ни разу не попали по кораблю, либо у нас есть только убитые корабли), 
            # то мы будем выбирать последовательность подряд идущих пустых клеток, выбирать элемент посередине,
            # смотреть, сколько пустых клеток рядом с ним на противоположной оси и считать его баллы 
            # баллы складываются так - сумма подряд идущих пустых клеток в основной оси и пустых клеток в противоположной оси
            
            # сначала пройдемся по всем горизонтальным осям и посчитаем максимальное количество баллов у каждой клетки
            if len([*self.comp_hits.values()]) == 0:
                mnj1 = 0 # номер столбца с котрого начинается максимальное количетво подряд идущих пустых клеток в первом цикле 
                i1 = 0 # номер строки элемента с максимальным баллом в первом цикле
                mc1 = 0 # максимальное количетво подряд идущих пустых клеток в первом цикле 
                moc1 = 0 # колличество баллов в первом цикле (сумма максимального количетва подряд идущих пустых клеток с пустыми клетками в другой оси)

                checkX = self.generateCheckOppositeAxis('X')
                checkY = self.generateCheckOppositeAxis('Y')

                for i in range(10):
                    nc = 0 # количество подряд идущих пустых клеток
                    is_exit = False # нужно ли выходить из цикла
                    
                    for j in range(10):
                       
                        # проверяем пустая ли у нас клетка, если да, то увеличиваем счетчик, считаем баллы и сравниваем с максимальным количестовм баллов
                        if not("my_"+str(i)+"_"+str(j) in self.comp_shoots):           
                            nc += 1
                            if nc + checkX(i, math.ceil((j - nc + 1 + j) / 2)) >= moc1:
                                moc1 = nc + checkX(i, math.ceil((j - nc + 1 + j) / 2))
                                mc1 = nc
                                i1 = i
                                mnj1 = j - mc1 + 1
                            
                            # если клетка набрала 10 баллов, можно выходить из цикла, так это максимально количество баллов
                            if moc1 == 10:
                                is_exit = True
                                break

                            # если количетво подряд идущих пустых клеток >= 6 будем считать это за максимальное количество
                            # и переходить к след. клетке
                            if nc >= 6:
                                nc = 0
                                continue
                        #если мы уже стреляли в клетку - обнуляем счетчик
                        else:
                            nc = 0
                    
                    if is_exit == True:
                        break

                j2 = 0 # номер стоки с котрого начинается максимальное количетво подряд идущих пустых клеток во втором цикле 
                mni2 = 0 # номер столбца элемента с максимальным баллом во втором цикле 
                mc2 = 0 # максимальное количетво подряд идущих пустых клеток во втором цикле 
                moc2 = 0 # колличество баллов во втором цикле (сумма максимального количетва подряд идущих пустых клеток с пустыми клетками в другой оси)

                # теперь пройдемся по всем вертикальным осям и посчитаем максимальное количество баллов у каждой клетки
                for j in range(10):
                    nc = 0 # количество подряд идущих пустых клеток
                    is_exit = False # нужно ли выходить из цикла
                    
                    for i in range(10):
                       
                        # проверяем пустая ли у нас клетка, если да, то увеличиваем счетчик, считаем баллы и сравниваем с максимальным количестовм баллов
                        if not("my_"+str(i)+"_"+str(j) in self.comp_shoots):           
                            nc += 1
                            if nc + checkY(math.ceil((i - nc + 1 + i) / 2), j) >= moc2:
                                moc2 = nc + checkY(math.ceil((i - nc + 1 + i) / 2), j)
                                mc2 = nc
                                j2 = j
                                mni2 = i - mc2 + 1
                            
                            # если клетка набрала 10 баллов, можно выходить из цикла, так это максимально количество баллов
                            if moc1 == 10:
                                is_exit = True
                                break

                            # если количетво подряд идущих пустых клеток >= 6 будем считать это за максимальное количество
                            # и переходить к след. шагу
                            if nc >= 6:
                                nc = 0
                                continue
                        else:
                            nc = 0
                    if is_exit == True:
                        break

                # сравниваем макс. кол-во баллов в первом и втором цикле
                if moc2 > moc1:
                   i = math.ceil((mni2 +  (mni2 + mc2 - 1)) / 2)
                   j = j2
                else:
                    i = i1
                    j = math.ceil((mnj1 +  (mnj1 + mc1 - 1)) / 2)

            # если в словаре попадиний что-то есть, значит мы не добили корабль, будем стрелять рядом с удачным выстрелом
            else:
                points_around = []
                comp_first_hits = [*self.comp_hits.values()][0] # берем из словоря попаданий самы первый корабль, в котро мы попали

                # если в массиве попадиний 1 элемент будем выбирать клетку рядом и если мы в нее не стреляли до этого, будем стрелять в нее          
                if len(comp_first_hits) == 1:

                    i = int(comp_first_hits[0].split("_")[1])
                    j = int(comp_first_hits[0].split("_")[2])
                    
                    if i+1 <= 9 and not("my_"+str(i+1)+"_"+str(j) in self.comp_shoots):
                        points_around.append([i+1,j])
                    elif i-1 >= 0 and not("my_"+str(i-1)+"_"+str(j) in self.comp_shoots):
                        points_around.append([i-1,j])
                    elif j+1 <= 9 and not("my_"+str(i)+"_"+str(j+1) in self.comp_shoots):
                        points_around.append([i,j+1])
                    elif j-1 >= 0 and not("my_"+str(i)+"_"+str(j-1) in self.comp_shoots):
                        points_around.append([i,j-1])

                # если в массиве попадиний несколько элементов, найдем ось, на которой у нас есть попадания
                # на этой оси выбираем самую маленькую и большую клетки, 
                # смотрим стреляли ли мы рядом с ними, если нет то стреляем туда
                else:

                    # для того, чтобы узнать на какой оси у нас есть попадания, мы выбираем два элемента из массива 
                    i1 = int(comp_first_hits[0].split("_")[1])
                    j1 = int(comp_first_hits[0].split("_")[2])

                    i2 = int(comp_first_hits[1].split("_")[1])
                    j2 = int(comp_first_hits[1].split("_")[2])

                    # сравниваем значение горизонтальных осей элементов 
                    if i1 == i2:
                        # если они равны, то по вертикальным осям берем самый маленький и самый большой элементы
                        jl = int(sorted(comp_first_hits, key=lambda hit: int(hit.split("_")[2]))[-1].split("_")[2])
                        jf = int(sorted(comp_first_hits, key=lambda hit: int(hit.split("_")[2]))[0].split("_")[2])

                        # берем от самого маленького элемента предыдущий и смотрим не стреляли ли мы туда, если нет, то добавляем в массив
                        if i1>=0 and i1<=9 and jf-1>=0 and jf-1<=9 and not("my_"+str(i1)+"_"+str(jf-1) in self.comp_shoots):
                            points_around.append([i1,jf-1])
                        
                        # берем от самого большого элемента следующий и смотрим не стреляли ли мы туда, если нет, то добавляем в массив
                        elif i1>=0 and i1<=9 and jl+1>=0 and jl+1<=9 and not("my_"+str(i1)+"_"+str(jl+1) in self.comp_shoots):
                            points_around.append([i1,jl+1])
                            
                        # если все еще нет клетки в которую компьютер не стрелял, то точки попаданий находятся по кряаям,
                        # поэтому будем проверять клетки между попаданиями
                        #  ->     <-
                        # [x][][][x]
                        elif i1>=0 and i1<=9 and jf+1>=0 and jf+1<=9 and not("my_"+str(i1)+"_"+str(jf+1) in self.comp_shoots):
                            points_around.append([i1,jf+1])

                        elif i1>=0 and i1<=9 and jl-1>=0 and jl-1<=9 and not("my_"+str(i1)+"_"+str(jl-1) in self.comp_shoots):
                            points_around.append([i1,jl-1])

                        else:
                            points_around.append([i1,jf+2])
                    
                    # елси по горизонтальным осям не совпало, смотрим по вертикальным и делаем то же самое
                    elif j1 == j2:
                        il = int(sorted(comp_first_hits, key=lambda hit: int(hit.split("_")[1]))[-1].split("_")[1])
                        ifst = int(sorted(comp_first_hits, key=lambda hit: int(hit.split("_")[1]))[0].split("_")[1])

                        if ifst-1>=0 and ifst-1<=9 and j1>=0 and j1<=9 and not("my_"+str(ifst-1)+"_"+str(j1) in self.comp_shoots):
                            points_around.append([ifst-1,j1])

                        elif il+1>=0 and il+1<=9 and j1>=0 and j1<=9 and not("my_"+str(il+1)+"_"+str(j1) in self.comp_shoots):
                            points_around.append([il+1,j1])

                        elif ifst+1>=0 and ifst+1<=9 and j1>=0 and j1<=9 and not("my_"+str(ifst+1)+"_"+str(j1) in self.comp_shoots):
                            points_around.append([ifst+1,j1])

                        elif il-1>=0 and il-1<=9 and j1>=0 and j1<=9 and not("my_"+str(il-1)+"_"+str(j1) in self.comp_shoots):
                            points_around.append([il-1,j1])

                        else: 
                            points_around.append([ifst+2,j1])
                    
                select = randrange(len(points_around))
                i = points_around[select][0]
                j = points_around[select][1]  

            xn = j*self.gauge + (j+1)*self.indent + self.offset_x_user
            yn = i*self.gauge + (i+1)*self.indent + self.offset_y
            hit_status = 0

            n = 0
            for obj in self.fleet_user:
                n += 1
                print(obj.coord_map)
                if "my_"+str(i)+"_"+str(j) in obj.coord_map:

                    hit_status = 1 #изменить статус попадания
                    self.paintCross(xn,yn,"my_"+str(i)+"_"+str(j)) #мы попали, поэтому надо нарисовать крест
                    playsound("./sounds/vzryv.wav", block=False) #включаем звук попадания
                  
                    self.comp_shoots.append("my_"+str(i)+"_"+str(j)) #добавить точку в список выстрелов компьютера

                    if not(n in self.comp_hits):
                        self.comp_hits[n] = []
                    self.comp_hits[n].append("my_"+str(i)+"_"+str(j))

                    if obj.shoot("my_"+str(i)+"_"+str(j)) == 2:
                        hit_status = 2
                        obj.death = 1
                        self.comp_hits.pop(n)
                        for point in obj.around_map:
                            self.paintMiss(point)
                            self.comp_shoots.append(point)
                    break
          
            print("hit_status",hit_status)
            if hit_status == 0:
                self.comp_shoots.append("my_"+str(i)+"_"+str(j))
                self.paintMiss("my_"+str(i)+"_"+str(j))
                playsound("./sounds/vsplesk.wav", block=False)
                self.whose_move = "user"
            else:
                if self.checkFinish("comp") < 10:
                    if hit_status == 1:
                        step += 1
                        if step > 4:
                            Thread(target=self.compPlay, args=(0,)).start()
                        else:
                            Thread(target=self.compPlay, args=(step,)).start()
                    else:
                        Thread(target=self.compPlay, args=(0,)).start()
                else:
                   
                    showinfo("Морской бой", "Вы проиграли!")  

    def renderGameStartButton(self):
        #удалить кнопку, если она была
        try:
            self.b.destroy()
        except AttributeError:
            print(AttributeError)

        bttn_text = "Начать заново" if self.is_game_start else "Начать игру"
        bttn_y = 0.9 if self.is_game_start else 0.4

        self.b = Button(text = bttn_text, padx = "12", pady = "6", font = "16", bg = "#fff", relief = "solid", activebackground = "#F5F5F5", command = self.new_game)
        self.b.place(relx=0.5, rely=bttn_y, anchor="c", bordermode=OUTSIDE)
    
    #метод для игры пользователя
    def userPlay(self,e):
        if(self.whose_move == 'user'):
            for i in range(10):
                for j in range(10):
                    xn = j*self.gauge + (j+1)*self.indent + self.offset_x_comp
                    yn = i*self.gauge + (i+1)*self.indent + self.offset_y
                    xk = xn + self.gauge
                    yk = yn + self.gauge
                    if e.x >= xn and e.x <= xk and e.y >= yn and e.y <= yk and not("nmy_"+str(i)+"_"+str(j) in self.user_shoots):
                        hit_status = 0
                        for obj in self.fleet_comp:
                            #если координаты точки совпадают с координатой корабля, то вызвать метод выстрела
                            if "nmy_"+str(i)+"_"+str(j) in obj.coord_map:
                                hit_status = 1
                                self.paintCross(xn,yn,"nmy_"+str(i)+"_"+str(j))
                                self.user_shoots.append("nmy_"+str(i)+"_"+str(j))
                                playsound("./sounds/vzryv.wav", block=False)   #включаем звук попадания
                                #если метод вернул двойку, значит, корабль убит
                                if obj.shoot("nmy_"+str(i)+"_"+str(j)) == 2:
                                    obj.death = 1
                                    for point in obj.around_map:
                                        self.paintMiss(point)
                                        self.user_shoots.append(point)
                                break
                        #если статус попадания остался равным нулю - значит, мы промахнулись, передать управление компьютеру
                        #иначе дать пользователю стрелять
                        if hit_status == 0:
                            self.user_shoots.append("nmy_"+str(i)+"_"+str(j))
                            self.paintMiss("nmy_"+str(i)+"_"+str(j))
                            playsound("./sounds/vsplesk.wav", block=False)
                            self.whose_move = "comp"
                            #проверить выигрыш, если его нет - передать управление компьютеру
                            if self.checkFinish("user") < 10:
                                self.whose_move = 'comp'
                                Thread(target=self.compPlay, args=(0,)).start()
                        #после всех проверок еще раз проверяем выигрыш, если есть - выводим сообщение о выигрыше        
                        if self.checkFinish("user") >= 10: 
                            showinfo("Морской бой", "Вы выиграли!")
                        break

    def checked (self, *args):
        self.comp_level = self.levels_dif.get()

    def save_settings(self):
        self.config.set('game_settings', 'difficulty', self.comp_level)

        with open('settings.ini', 'w') as configfile:
            self.config.write(configfile)


    def __init__(self, master=None):
        atexit.register(self.save_settings)
        
        self.root = master
        Frame.__init__(self, self.root)
        self.pack()
        self.renderGameStartButton()   

        self.config = configparser.ConfigParser()
        self.config.read('settings.ini')
  
        self.comp_level = self.config.get('game_settings', 'difficulty')

        #инициализация меню
        self.m = Menu(master)
        self.root.config(menu = self.m)

        self.m_play = Menu(self.m)
        self.m_play.add_command(label="Новая игра", command = self.new_game)

        self.levels_dif = StringVar()
        self.levels_dif.set(self.comp_level)
        self.levels_dif.trace("w", self.checked)

        self.m_difficulty_levels = Menu(self.m, tearoff=0)
        self.m_difficulty_levels.add_radiobutton(label="Легко", value="easy", variable=self.levels_dif)
        self.m_difficulty_levels.add_radiobutton(label="Сложно", value="hard", variable=self.levels_dif)

        self.m.add_cascade(label = "Игра", menu = self.m_play)                        
        self.m.add_cascade(label="Уровень сложности", menu=self.m_difficulty_levels)