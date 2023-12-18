import heapq
import copy 
import time
import sys
rows, cols = 9, 12
ship_layout = [[0 for _ in range(cols)] for _ in range(rows)]

repeated_layout = []

#Stores the traceback
global_traceback = []

heap = []
heapq.heapify(heap)
with open("sample.txt", "r") as file:
    for item in file:
        item = item.strip()
        if item:
            line = item.replace('[', '').replace(']', '').replace('{', '').replace('}', '')
            line = line.split(",")
            line1 = int(line[0]) - 1
            if(line1 > rows - 1):
                print("Reached Row Limit")
                sys.exit()
            line2 = int(line[1]) - 1
            if(line2 > cols - 1):
                print("Reached Col Limit")
                sys.exit()
            line3 = line[2].strip()
            ship_layout[line1][line2] = int(line3)
            if str(line[3].strip()) == "NAN":
                ship_layout[line1][line2] = 'X'

class balance:
    def __init__(self, layout):
        self.layout = layout
        self.cost = 0
        self.score = 0
        self.initial_row = 0
        self.initial_col = 0
        self.destination_row = 0
        self.destination_col = 0
        self.traceback = []  # list of tuples to store the path

    def __lt__(self, other):
        return self.score < other.score

    def left_weight(self):
        weight = 0
        for i in range(rows):  # left_weight
            for j in range(int(cols / 2)):
                if isinstance(self.layout[i][j], int):
                    weight += self.layout[i][j]
        return weight

    def right_weight(self):
        weight = 0
        for i in range(rows):  # right_weight
            for j in range(int(cols / 2), cols):
                if isinstance(self.layout[i][j], int):
                    weight += self.layout[i][j]
        return weight

    def balance_mass(self):
        total_weight = self.left_weight() + self.right_weight()
        return total_weight / 2

    def deficit(self):
        defic = self.balance_mass() - min(self.left_weight(), self.right_weight())
        return defic

    def find_highest_container(self, column):
        temp = True
        counter = rows - 1
        while temp:
            if self.layout[counter][column] != 0 or self.layout[counter][column] == 'X':
                temp = False
            else:
                counter = counter - 1
                if counter < 0:
                    temp = False
        return counter

    def get_heuristic(self):
        sorted_arr = []
        if self.left_weight() > self.right_weight():
            for i in range(rows):
                for j in range(int(cols / 2)):
                    if isinstance(self.layout[i][j], int) and self.layout[i][j] != '0' and self.layout[i][j] != 0:
                        sort = [self.layout[i][j], j]
                        sorted_arr.append(sort)
            s = sorted(sorted_arr, reverse=True)
        else:
            for i in range(rows):
                for j in range(int(cols / 2), int(cols)):
                    if isinstance(self.layout[i][j], int) and self.layout[i][j] != '0' and self.layout[i][j] != 0:
                        sort = [self.layout[i][j], j]
                        sorted_arr.append(sort)
            s = sorted(sorted_arr, reverse=True)

        if self.right_weight() > self.left_weight():
            for i in range(rows):
                for j in range(int(cols / 2)):
                    if isinstance(self.layout[i][j], int) and self.layout[i][j] != '0' and self.layout[i][j] != 0:
                        sort = [self.layout[i][j], j]
                        sorted_arr.append(sort)
            s = sorted(sorted_arr, reverse=True)
        else:
            for i in range(rows):
                for j in range(int(cols / 2), int(cols)):
                    if isinstance(self.layout[i][j], int) and self.layout[i][j] != '0' and self.layout[i][j] != 0:
                        sort = [self.layout[i][j], j]
                        sorted_arr.append(sort)
            s = sorted(sorted_arr, reverse=True)

        deficit_val = self.deficit()
        used_arr = []
        for i in range(0, len(s), 1):
            if s[i][0] <= deficit_val:
                deficit_val = deficit_val - s[i][0]
                new_row = s[i]
                used_arr.append(new_row)
        return len(used_arr)

    def new_nearest_neighbor(self, balance_object, heap):
        H = self.get_heuristic()
        c_cost = 0
        r_cost = 0

        for i in range(0, cols, 1):
            if balance_object.find_highest_container(i) == -1:
                continue
            if balance_object.layout[balance_object.find_highest_container(i)][i] == 'X':
                continue
            if balance_object.layout[balance_object.find_highest_container(i)][i] == 0 or \
                    balance_object.layout[balance_object.find_highest_container(i)][i] == '0':
                continue

            for j in range(0, cols, 1):
                if j == i:
                    continue
                copy_object = copy.deepcopy(balance_object)
                highest_container_row = copy_object.find_highest_container(i)
                next_highest_container_row = copy_object.find_highest_container(j)
                if next_highest_container_row == rows - 1:
                    continue
                copy_object.layout[next_highest_container_row + 1][j] = \
                    copy_object.layout[highest_container_row][i]

                copy_object.layout[highest_container_row][i] = 0
                copy_object.initial_row = highest_container_row
                copy_object.initial_col = i
                copy_object.destination_row = next_highest_container_row + 1  # Fixing the row index
                copy_object.destination_col = j

                col_cost = abs(i - (j))
                row_cost = abs(highest_container_row - next_highest_container_row)

                H = copy_object.get_heuristic()
                copy_object.cost = col_cost + row_cost + copy_object.cost
                copy_object.score = H + copy_object.cost

                copy_object.traceback.append(
                    (copy_object.initial_row, copy_object.initial_col, copy_object.destination_row,
                    copy_object.destination_col))

                heapq.heappush(heap, copy_object)

    def algorithm(self, original):
        start_time = time.time()
        original.score = original.get_heuristic()
        heapq.heappush(heap, original)

        original.layout = original.layout[::-1]
        print("initial")
        for i in range(rows):
            print(original.layout[i])
            #Reverse for Traceback (Each step in curr_obj)
            original.layout = original.layout[::-1]
        if not original.doable():
            return
        while True:
            if len(heap) == 0:
                return
            curr_obj = heapq.heappop(heap)
            if curr_obj.goal_state():
                curr_obj.layout = curr_obj.layout[::-1]
                print("final")
                for i in range(rows):
                    print(curr_obj.layout[i])
                #Reverse for Traceback (Each step in curr_obj)
                curr_obj.layout = curr_obj.layout[::-1]

                #set up the global_traceback so it can be used by another function
                global_traceback.extend(curr_obj.traceback)

                # print("\nTraceback:")
                # #for step in curr_obj.traceback:
                # for step in global_traceback:
                #     print(f"Move from ({step[0]+1}, {step[1]+1}) to ({step[2]+1}, {step[3]+1})")
                end_time = time.time()
                elapsed_time = end_time - start_time
                print("elapsed_time: " + str(elapsed_time))
                return
            else:
                curr_obj.new_nearest_neighbor(curr_obj, heap)

    def goal_state(self):
        left_weight = 0
        right_weight = 0
        for i in range(rows):
            for j in range(int(cols / 2)):
                if isinstance(self.layout[i][j], int):
                    left_weight += self.layout[i][j]

        for i in range(rows):
            for j in range(int(cols / 2), cols):
                if isinstance(self.layout[i][j], int):
                    right_weight += self.layout[i][j]

        return min(left_weight, right_weight) / max(left_weight, right_weight) > 0.9

    def doable(self):
        total = self.left_weight() + self.right_weight()
        for i in range(rows):
            for j in range(int(cols)):
                if isinstance(self.layout[i][j], int) and self.layout[i][j] != '0' and self.layout[i][j] != 0:
                    if not total - self.layout[i][j] >= self.layout[i][j] * 0.9:
                        print("Not Doable")
                        return False
                    #flying weights
                    if(i > 0):
                        if(self.layout[i-1][j] == 0 or self.layout[i-1][j] == '0'):
                            print("Flying Weight, Not Doable")
                            return False
        return True


# MAKE THIS BALANCE BUTTON?
ship = balance(ship_layout)


#ship.algorithm(ship)

#Displaying the traceback source to destination
#print("\nGlobal Traceback:")
for step in global_traceback:
    print(f"Move from ({step[0]+1}, {step[1]+1}) to ({step[2]+1}, {step[3]+1})")
"""
#Test sample1, sample2, sample3
#case 1: finds correct highest row even if 'NAN'
#case 2: row limit
#case 3: col limit
ship.layout = ship.layout[::-1]
print("sample")
for i in range(rows):
    print(ship.layout[i])
#Reverse for Traceback (Each step in curr_obj)
ship.layout = ship.layout[::-1]"""
"""
#sample 1
ship_layout1 = [[0 for _ in range(cols)] for _ in range(rows)]
print("sample 1")
with open("sample.txt", "r") as file:
    for item in file:
        item = item.strip()
        if item:
            line = item.replace('[', '').replace(']', '').replace('{', '').replace('}', '')
            line = line.split(",")
            line1 = int(line[0]) - 1
            if(line1 > rows - 1):
                print("Reached Row Limit")
                sys.exit()
            line2 = int(line[1]) - 1
            if(line2 > cols - 1):
                print("Reached Col Limit")
                sys.exit()
            line3 = line[2].strip()
            ship_layout1[line1][line2] = int(line3)
            if str(line[3].strip()) == "NAN":
                ship_layout1[line1][line2] = 'X'

ship1 = balance(ship_layout1)
#ship1.algorithm(ship1)

print(ship1.find_highest_container(0))#col 0, test case where highest row = 1, recognize 'NAN', returns row - 1, should return 0
print(ship1.find_highest_container(1))#col 1, test case where highest row = 9, meaning full, returns row - 1, should return 8
print(ship1.find_highest_container(2))#col 2, test case where highest row = 9, meaning full, returns row - 1, should return 8
print(ship1.find_highest_container(3))#col 3, test case where highest row = 8, returns row - 1, should return 7
print(ship1.find_highest_container(4))#col 4, test case where highest row = 7, returns row - 1, should return 6
print(ship1.find_highest_container(5))#col 5, test case where highest row = 6, returns row - 1, should return 5
print(ship1.find_highest_container(6))#col 6, test case where highest row = 5, returns row - 1, should return 4
print(ship1.find_highest_container(7))#col 7, test case where highest row = 4, returns row - 1, should return 3
print(ship1.find_highest_container(8))#col 8, test case where highest row = 3, returns row - 1, should return 2
print(ship1.find_highest_container(9))#col 9, test case where highest row = 2, returns row - 1, should return 1
print(ship1.find_highest_container(10))#col 10, test case where highest row = 1, returns row - 1, should return 0 
print(ship1.find_highest_container(11))#col 11, test case where highest row = 0, returns row - 1, should return -1, means empty col

#sample 2
print("sample 2")
ship_layout2 = [[0 for _ in range(cols)] for _ in range(rows)]
with open("sample2.txt", "r") as file:
    for item in file:
        item = item.strip()
        if item:
            line = item.replace('[', '').replace(']', '').replace('{', '').replace('}', '')
            line = line.split(",")
            line1 = int(line[0]) - 1
            if(line1 > rows - 1):
                print("Reached Row Limit")
                sys.exit()
            line2 = int(line[1]) - 1
            if(line2 > cols - 1):
                print("Reached Col Limit")
                sys.exit()
            line3 = line[2].strip()
            ship_layout2[line1][line2] = int(line3)
            if str(line[3].strip()) == "NAN":
                ship_layout2[line1][line2] = 'X'

ship2 = balance(ship_layout2)
ship2.algorithm(ship2)

#sample 3
print("sample 3")
ship_layout2 = [[0 for _ in range(cols)] for _ in range(rows)]
with open("sample3.txt", "r") as file:
    for item in file:
        item = item.strip()
        if item:
            line = item.replace('[', '').replace(']', '').replace('{', '').replace('}', '')
            line = line.split(",")
            line1 = int(line[0]) - 1
            if(line1 > rows - 1):
                print("Reached Row Limit")
                sys.exit()
            line2 = int(line[1]) - 1
            if(line2 > cols - 1):
                print("Reached Col Limit")
                sys.exit()
            line3 = line[2].strip()
            ship_layout2[line1][line2] = int(line3)
            if str(line[3].strip()) == "NAN":
                ship_layout2[line1][line2] = 'X'

ship2 = balance(ship_layout2)
ship2.algorithm(ship2)
"""
"""
#sample 4

print("sample 4")
ship_layout4 = [[0 for _ in range(cols)] for _ in range(rows)]
with open("sample4.txt", "r") as file:
    for item in file:
        item = item.strip()
        if item:
            line = item.replace('[', '').replace(']', '').replace('{', '').replace('}', '')
            line = line.split(",")
            line1 = int(line[0]) - 1
            if(line1 > rows - 1):
                print("Reached Row Limit")
                sys.exit()
            line2 = int(line[1]) - 1
            if(line2 > cols - 1):
                print("Reached Col Limit")
                sys.exit()
            line3 = line[2].strip()
            ship_layout4[line1][line2] = int(line3)
            if str(line[3].strip()) == "NAN":
                ship_layout4[line1][line2] = 'X'

ship4 = balance(ship_layout4)
ship4.algorithm(ship4)
"""
"""
#sample 5
print("sample 5")
ship_layout5 = [[0 for _ in range(cols)] for _ in range(rows)]
with open("sample5.txt", "r") as file:
    for item in file:
        item = item.strip()
        if item:
            line = item.replace('[', '').replace(']', '').replace('{', '').replace('}', '')
            line = line.split(",")
            line1 = int(line[0]) - 1
            if(line1 > rows - 1):
                print("Reached Row Limit")
                sys.exit()
            line2 = int(line[1]) - 1
            if(line2 > cols - 1):
                print("Reached Col Limit")
                sys.exit()
            line3 = line[2].strip()
            ship_layout5[line1][line2] = int(line3)
            if str(line[3].strip()) == "NAN":
                ship_layout5[line1][line2] = 'X'

ship5 = balance(ship_layout5)
ship5.algorithm(ship5)
"""