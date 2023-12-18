import sys
import numpy as np
from datetime import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QGridLayout, QVBoxLayout, QWidget, QPushButton, QFileDialog, QLabel, QLineEdit, QDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
################################################################################################################################
#Balancing Portion
import re
import heapq
import copy

#Global file path
selected_file_path=""

#global shipbay size
rows, cols = 9, 12

#ship_layout = [[0 for _ in range(cols)] for _ in range(rows)]
orig_containers = []

global_layout = []

repeated_layout = []

#Stores the traceback
global_traceback = []

heap = []
heapq.heapify(heap)

class Balance:
    def __init__(self, rows, cols):
        self.layout = [[0 for _ in range(cols)] for _ in range(rows)]
        self.cost = 0
        self.score = 0
        self.initial_row = 0
        self.initial_col = 0
        self.destination_row = 0
        self.destination_col = 0
        self.traceback = []  # list of tuples to store the path

    def read_ship_layout(self):
        global selected_file_path
        # file_dialog = QFileDialog()
        # file_dialog.setWindowTitle("Select Ship Layout File")
        # file_dialog.setFileMode(QFileDialog.ExistingFile)
        # file_dialog.setNameFilter("Text files (*.txt)")

        # if file_dialog.exec() == QFileDialog.Accepted:
        #     file_path = file_dialog.selectedFiles()[0]

        #indent once if comments above are removed
        with open(selected_file_path, "r") as file:
            for item in file:
                item = item.strip()
                if item:
                    line = item.replace('[', '').replace(']', '').replace('{', '').replace('}', '')
                    line = line.split(",")
                    line1 = int(line[0]) - 1
                    line2 = int(line[1]) - 1
                    line3 = line[2].strip()
                    self.layout[line1][line2] = int(line3)
                    if str(line[3].strip()) == "NAN":
                        self.layout[line1][line2] = 'X'

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
            if balance_object.layout[balance_object.find_highest_container(i)][i] == 0 or balance_object.layout[balance_object.find_highest_container(i)][i] == '0':
                continue

            for j in range(0, cols, 1):
                if j == i:
                    continue
                copy_object = copy.deepcopy(balance_object)
                highest_container_row = copy_object.find_highest_container(i)
                next_highest_container_row = copy_object.find_highest_container(j)
                if next_highest_container_row == rows - 1:
                    continue
                copy_object.layout[next_highest_container_row + 1][j] = copy_object.layout[highest_container_row][i]

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

    #def algorithm(self, original):
    def algorithm(self, original):
        global global_traceback
        original.score = original.get_heuristic()
        heapq.heappush(heap, original)
        repeated_layout.append(original.layout)
        if not original.doable():
            return
        while True:
            if len(heap) == 0:
                return
            curr_obj = heapq.heappop(heap)
            if curr_obj.goal_state():
                """curr_obj.layout = curr_obj.layout[::-1]
                print("final")
                for i in range(rows):
                    print(curr_obj.layout[i])
                #Reverse for Traceback (Each step in curr_obj)
                curr_obj.layout = curr_obj.layout[::-1]"""

                #set up the global_traceback so it can be used by another function
                global_traceback.extend(curr_obj.traceback)

                # print("\nTraceback:")
                # #for step in curr_obj.traceback:
                # for step in global_traceback:
                #     print(f"Move from ({step[0]+1}, {step[1]+1}) to ({step[2]+1}, {step[3]+1})")

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
        return True

################################################################################################################################
#For every line in the manifest.txt file, parse out the values
def parse_container_line(line):
    #line example: [01,01], {99999}, Walmart
    
    line = line.strip()  # Remove only the end line \n
    if ", " not in line:
    # If the expected format is not found, handle it accordingly
        print(f"Invalid line format: {line}")
        return None

    coords, weight, name = line.split(", ")

    # Extracting x, y coordinates
    x, y = map(int, coords[1:-1].split(","))
    # Remove curly braces from weight, convert to int
    weight = int(weight[1:-1])

    # Returns a tuple of int, int, int, str
    return x, y, weight, name

#Reading the ship manifest text file from file explorer
def read_ship_manifest(file_path):
    containers = []
    with open(file_path, 'r') as file:
        for line in file:
            containers.append(parse_container_line(line))
        append_ninth(containers)
    return containers #each container is now broken down and in a tuple

#Appends the ninth row that can be used temporarily
def append_ninth(containers):
    for i in range(1,13):
        containers.append((9,i,0,'UNUSED')) #Appending UNUSED tuples for 9th row
    return containers

#Displays the ship bay
def display_ship(containers):
    fig, ax = plt.subplots(figsize=(12, 9))

    for x, y, weight, name in containers:
        if 1 <= y <= 12 and 1 <= x <= 9:
            if name == "NAN":
                color = 'gray'
            elif name == "UNUSED":
                color = 'white'
            else:
                color = 'lightblue'
                #ax.text displays the first 3 characters of a containers name in the grid(only applied to lightblue)
                ax.text(y - 0.5, x - 0.5, name[:3], ha='center', va='center', fontsize=12, color='black')
            #Creates the individual container and fills in the color depending on the name, NAN, or UNUSED
            ax.add_patch(plt.Rectangle((y-1, x-1), 1, 1, facecolor=color, edgecolor='black'))

            #print(name," - Patch added at [",x,",",y,"] with color=",color,".")

    # Hide major tick labels
    ax.set_xticklabels('')
    ax.set_yticklabels('')

    # Customize minor tick labels, (ticks at x.5 sets to center, and then replace with whole integer)
    ax.set_xticks([0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12],      minor=True)
    ax.set_xticklabels(['1','2','3','4','5','6','7','8','9','10','11','12',''], minor=True)

    ax.set_yticks([0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9],      minor=True)
    ax.set_yticklabels(['1','2','3','4','5','6','7','8','9',''], minor=True)

    ax.grid(color='black', linestyle='-', linewidth=1)
    ax.set_title('Ship Bay Display')
    #plt.show()

    return fig

class LoginPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Login")
        self.setGeometry(200, 200, 300, 100)

        self.layout = QVBoxLayout()

        self.label = QLabel("Enter Full Name:")
        self.name_input = QLineEdit(self)
        self.login_button = QPushButton("Login", self)
        self.login_button.clicked.connect(self.accept_login)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.name_input)
        self.layout.addWidget(self.login_button)

        self.setLayout(self.layout)
        
    def accept_login(self):
        full_name = self.name_input.text()
        self.accept()

class CommentPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Comment")
        self.setGeometry(200, 200, 300, 100)

        self.layout = QVBoxLayout()

        self.label = QLabel("Enter your comment:")
        self.text_input = QLineEdit(self)
        self.comment_button = QPushButton("Comment", self)
        self.comment_button.clicked.connect(self.accept_comment)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.text_input)
        self.layout.addWidget(self.comment_button)

        self.setLayout(self.layout)
        
    def accept_comment(self):
        full_comment = self.text_input.text()
        self.accept()

class ShipDisplayApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Port Organizer Solutions")

        self.balance = Balance(rows=9, cols=12)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        #self.layout = QVBoxLayout(self.central_widget)
        self.layout = QGridLayout(self.central_widget)

        self.choose_file_button = QPushButton("Choose File")
        self.choose_file_button.clicked.connect(self.choose_file)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.show_login_popup)

        self.comment_button = QPushButton("Comment")
        self.comment_button.clicked.connect(self.show_comment_popup)

        initial_button = 0
        self.balance_button = QPushButton("Run Balance")
        if(initial_button == 0):
            print("run")
            self.balance_button.clicked.connect(self.run_balance)
            initial_button == 1
        else:
            print("show")
            self.balance_button.clicked.connect(self.show_next_step)

        # Add a counter to keep track of the current step
        self.current_step = 0
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.show_next_step)

        #self.next_button.setEnabled(False) #Initially disabled until done w/ algo

        # Add a QLabel to display move information
        self.move_info_label = QLabel("", self)
        self.layout.addWidget(self.move_info_label, 3,1)

        #Display the first step
        #self.show_next_step()

        self.canvas = FigureCanvas(display_ship([]))

        self.layout.addWidget(self.choose_file_button, 0,0)
        self.layout.addWidget(self.login_button, 0,2)
        self.layout.addWidget(self.comment_button, 0,1)
        self.layout.addWidget(self.balance_button, 1,1)
        self.layout.addWidget(self.canvas, 2,0, 1,2)
        self.layout.addWidget(self.next_button, 3,2)

        #Store the global_traceback
        self.global_traceback=[]

    def choose_file(self):
        global selected_file_path
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open Ship Manifest File", "", "Text Files (*.txt)")
        if file_path:
            # Log the file open event
            self.log_event(f'The manifest, "{file_path}" , has been chosen.')

            #save the file path in the global variable
            selected_file_path = file_path
            self.global_traceback=[] #Reset the traceback when a new file is open
            self.next_button.setEnabled(False)
            self.canvas.figure = display_ship(read_ship_manifest(file_path))
            self.canvas.draw()

    def show_login_popup(self):
        login_popup = LoginPopup(self)
        result = login_popup.exec()
        if result == QDialog.Accepted:
            full_name = login_popup.name_input.text()
            #print(f"{full_name} has Logged in.")
            # Log the login event
            self.log_event(f'"{full_name}" has logged in.')

    def show_comment_popup(self):
        comment_popup = CommentPopup(self)
        result = comment_popup.exec()
        if result == QDialog.Accepted:
            full_comment = comment_popup.text_input.text()
            #print(f"{full_comment} has Logged in.")
            # Log the login event
            self.log_event(f'"{full_comment}"')

    def show_reminder_popup(self):
        # Display a popup reminding the user to send the new manifest by email
        reminder_popup = QDialog(self)
        reminder_popup.setWindowTitle("Reminder")
        reminder_popup.setGeometry(200, 200, 300, 100)

        layout = QVBoxLayout()

        label = QLabel("Don't forget to send the new manifest by email.")
        ok_button = QPushButton("OK", reminder_popup)
        ok_button.clicked.connect(reminder_popup.accept)

        layout.addWidget(label)
        layout.addWidget(ok_button)

        reminder_popup.setLayout(layout)
        # reminder_popup.exec()


    def get_containers_from_layout(self):#gets layout from file
        # Convert the ship layout to a list of containers
        containers = []
        original_containers = read_ship_manifest(selected_file_path)  # Get original containers

        for i in range(rows):
            for j in range(cols):
                if isinstance(self.balance.layout[i][j], int):
                    # Find the container in the original manifest
                    original_container = next(
                        (container for container in original_containers if container[0] == i + 1 and container[1] == j + 1),
                        None
                    )
                    if original_container:
                        # Use the name and weight from the original manifest
                        containers.append((i + 1, j + 1, original_container[2], original_container[3]))
        return containers

    def change_layout(self,layout):
        print("in")

        global global_containers

        step = global_traceback.pop(0)

        # Display the move in the console
        move_info = f"Move from ({step[0] + 1}, {step[1] + 1}) to ({step[2] + 1}, {step[3] + 1})"
        self.move_info_label.setText(move_info)
        self.log_event(move_info)

        initial = -1
        destination = -1
        for i in range(len(global_containers)):
            if (global_containers[i][0]-1 == step[0] and global_containers[i][1]-1 == step[1]):
                initial = i
            elif (global_containers[i][0]-1 == step[2] and global_containers[i][1]-1 == step[3]):
                destination = i
        if (not initial == -1 and not destination == -1):
            global_containers[destination] = (global_containers[destination][0], global_containers[destination][1], global_containers[initial][2], global_containers[initial][3])
            global_containers[initial] = (global_containers[initial][0], global_containers[initial][1], 0, 'UNUSED')


    def run_balance(self):
        print("in run_balance")
        global global_traceback
        self.balance.read_ship_layout()
        self.balance.algorithm(original=self.balance)

        # Display the initial ship state
        global global_containers
        global_containers = read_ship_manifest(selected_file_path)

        self.canvas.figure = display_ship(global_containers)
        self.canvas.draw()
        for step in global_traceback:
            print(f"Move1 from ({step[0]+1}, {step[1]+1}) to ({step[2]+1}, {step[3]+1})")
        
        # Enable Next button when traceback is not empty
        if global_traceback:
            self.next_button.setEnabled(True)
            print("true global_traceback")
            #self.show_next_step()
        else :
            self.next_button.setEnabled(False) #Initially disabled until done w/ algo

    def show_next_step(self):
        print("in show_next_step")
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.show_next_step)
        global global_traceback

        if not global_traceback:
            # No more steps, disable the Next button
            self.next_button.setEnabled(False)
            print("end")
            # Show reminder to send the new manifest to the ship by email.
            self.show_reminder_popup()
            return
        """
        step = global_traceback.pop(0)

        # Display the move in the console
        move_info = f"Move from ({step[0] + 1}, {step[1] + 1}) to ({step[2] + 1}, {step[3] + 1})"
        self.move_info_label.setText(move_info)
        self.log_event(move_info)"""

        self.change_layout(self.balance.layout)

        """
        # Update the ship layout based on the step
        self.balance.layout[step[2]][step[3]] = self.balance.layout[step[0]][step[1]]

        #print(str(step[2]) + " " +  str(step[3]) + " " + str(step[0]) + " " + str(step[1]))
        print(self.balance.layout[step[2]][step[3]])

        #self.balance.layout[step[0]][step[1]] = 0

        print(self.balance.layout[step[0]][step[1]])

        #self.change_layout(self.balance.layout)
        """
        # Redraw the ship display
        self.canvas.figure = display_ship(global_containers)
        self.canvas.draw()    
        # Save the new manifest with the changes
        self.save_outbound_manifest()
    
        #self.end_case() 

    def save_outbound_manifest(self):
        global selected_file_path

        # Create a new manifest file path for the outbound manifest
        outbound_file_path = selected_file_path.replace(".txt", "_OUTBOUND.txt")

        # Write the new manifest to the outbound file
        with open(outbound_file_path, "w") as outbound_file:
            for i in range(rows):
                for j in range(cols):
                    if isinstance(self.balance.layout[i][j], int) or self.balance.layout[i][j] == 'NAN':
                        # Convert container information to the manifest line format
                        container_name = f"Container {i * cols + j + 1}" if isinstance(self.balance.layout[i][j], int) else 'NAN'
                        manifest_line = f"[{i + 1:02d},{j + 1:02d}], {{{self.balance.layout[i][j]:05d}}}, {container_name}\n"
                        outbound_file.write(manifest_line)

        # Log the event
        self.log_event(f'The new manifest, "{outbound_file_path}" , has been generated.')

        # Display the reminder popup
        self.show_reminder_popup()

    #All text_file openings, logins, comments, and generation of *_OUTBOUND files will be logged.
    def log_event(self, event_message):
        # Log the event with a timestamp
        timestamp = datetime.now().strftime("%m/%d/%Y - %H:%M")
        log_entry = f'{timestamp} - {event_message}'

        # Print to console
        print(log_entry)

        # Write to log file
        with open('event_log.txt', 'a') as log_file:
            log_file.write(log_entry + '\n')

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = ShipDisplayApp()
    window.show()

    sys.exit(app.exec())