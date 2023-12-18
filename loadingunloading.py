import tkinter as tk
from tkinter import filedialog, simpledialog
from tkinter import messagebox
from charset_normalizer import set_logging_handler
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import heapq
import copy
import functools
import logging
import time

start_time = None
logging.basicConfig(filename='/Users/sreekarpraneethmarri/Amrita/Programming/operation_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Logging started.")
def log_function_call(func):
    @functools.wraps(func) 
    def wrapper(*args, **kwargs):
        arg_repr = [repr(a) for a in args]                  
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(arg_repr + kwargs_repr)     
        logging.info(f"Calling {func.__name__}({signature})")
        
        value = func(*args, **kwargs)

        logging.info(f"{func.__name__} returned {value!r}")
        return value
    return wrapper

@log_function_call
def parse_manifest(manifest):
    containers = []
    for line in manifest.split('\n'):
        if line.strip():
            parts = line.strip().split(', ')
            position = tuple(map(int, parts[0][1:-1].split(',')))
            weight = int(parts[1][1:-1])
            name = parts[2]
            containers.append({'position': position, 'weight': weight, 'name': name})
    return containers

class State:
    def __init__(self, containers, width, length, create_visualization_window, parent=None, cost=0, last_move=None):
        self.containers = containers
        self.width = width
        self.length = length
        self.parent = parent
        self.cost = cost
        self.last_move = last_move
        self.create_visualization_window = create_visualization_window

    def __lt__(self, other):
        return self.cost < other.cost
    
    @log_function_call
    def is_container_above(self, position):
        for container in self.containers:
            if container['position'][1] == position[1] and container['position'][0] > position[0] and container['name'] != 'UNUSED':
                return True, container, container['position']
        return False, None, None
    
    @log_function_call
    def display_path_with_visualization(self, target_container):
        new_window = self.create_visualization_window()
        fig, ax = plt.subplots()
        canvas = FigureCanvasTkAgg(fig, master=new_window)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack()

        path = []
        current_state = self
        while current_state:
            path.append(current_state)
            current_state = current_state.parent

        for state in reversed(path):
            state.draw_ship_layout(ax, target_container)
            canvas.draw()
            new_window.update()
            plt.pause(0.5)  
    
    @log_function_call
    def write_manifest(self, file_path):
        with open(file_path, 'w') as file:
            for container in self.containers:
                pos = container['position']
                weight = container['weight']
                name = container['name']
                file.write(f"({pos[0]},{pos[1]}), ({weight}), {name}\n")
    
    @log_function_call
    def get_neighbors(self, target_container):
        neighbors = []
        for i, container in enumerate(self.containers):
            if container['name'] == target_container:
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    new_row = container['position'][0] + dx
                    new_col = container['position'][1] + dy
                    if 1 <= new_row <= self.width and 1 <= new_col <= self.length:
                        if any(c['position'] == (new_row, new_col) and c['name'] == 'UNUSED' for c in self.containers):
                            new_containers = copy.deepcopy(self.containers)
                            new_containers[i] = {'position': (new_row, new_col), 'weight': container['weight'], 'name': container['name']}
                            for c in new_containers:
                                if c['position'] == container['position']:
                                    c['name'] = 'UNUSED'
                            neighbors.append((State(new_containers, self.width, self.length, self.create_visualization_window, self, self.cost + 1, (new_row, new_col)), 1))
        return neighbors
    
    @log_function_call
    def move_container_to_position(self, container_name, start_position, end_position, ax):
        current_position = start_position
        while current_position != end_position:
            next_position = list(current_position)
            if current_position[0] != end_position[0]:
                next_position[0] += 1 if end_position[0] > current_position[0] else -1
            elif current_position[1] != end_position[1]:
                next_position[1] += 1 if end_position[1] > current_position[1] else -1
            next_position = tuple(next_position)
            self.update_container_position(container_name, current_position, next_position)
            self.draw_ship_layout(ax, container_name)
            plt.pause(0.5)

            current_position = next_position
    
    @log_function_call
    def is_goal(self, target_container):
        for container in self.containers:
            if container['name'] == target_container:
                row, col = container['position']
                if row == self.width: 
                    return True
        return False
    
    @log_function_call
    def is_valid_position(self, position):
        if 1 <= position[0] <= self.width and 1 <= position[1] <= self.length:
            return not any(c['position'] == position and c['name'] != 'UNUSED' for c in self.containers)
        return False
    
    @log_function_call
    def calculate_loading_cost(self, position):
        entry_point = (1, 1)
        return abs(position[0] - entry_point[0]) + abs(position[1] - entry_point[1])

    @log_function_call
    def update_container_position(self, container_name, old_position, new_position):
        for container in self.containers:
            if container['name'] == container_name:
                container['position'] = new_position
            elif container['position'] == old_position:
                container['name'] = 'UNUSED'
            elif container['position'] == new_position:
                container['name'] = container_name
    
    @log_function_call
    def load_container(self, container_name, position, weight, ax):
        if not 1 <= position[1] <= self.length:
            print("Invalid position: out of ship's length.")
            return False, 0

        current_position = (self.width, position[1])

        for row in range(self.width, position[0] - 1, -1):
            if not self.is_valid_position((row, position[1])):
                print(f"Cannot load container: path to position {position} is blocked.")
                return False, 0

        steps = 1
        while current_position != position:
            next_position = (current_position[0] - 1, current_position[1])
            self.update_container_position(container_name, current_position, next_position)
            self.draw_ship_layout(ax, container_name)
            plt.pause(0.5) 
            current_position = next_position
            steps += 1
        self.containers.append({'position': position, 'weight': weight, 'name': container_name})

        plt.pause(1) 
        print(f"Container {container_name} loaded to {position} in {steps} steps.")
        return True, steps
    
    @log_function_call
    def load_and_visualize_process(self, container_name, position):
        fig, ax = plt.subplots()
        self.draw_ship_layout(ax, None)
        plt.pause(1)
        success, steps = self.load_container(container_name, position, ax)
        if success:
            print(f"Loading container '{container_name}' at position {position}.")
            print(f"Loading cost: {steps} steps.")
            self.draw_ship_layout(ax, container_name)
            plt.show()
        else:
            print("Invalid position for loading the container.")
            plt.close()
    
    @log_function_call
    def draw_ship_layout(self, ax, target_container):
        ax.clear()
        ax.set_xlim(0, self.length)
        ax.set_ylim(0, self.width)
        ax.set_xticks(range(self.length + 1))
        ax.set_yticks(range(self.width + 1))
        ax.grid(True)

        for container in self.containers:
            row, col = container['position']
            name = container['name']
            color = 'white' if name == 'UNUSED' else 'none'
            rect = patches.Rectangle((col - 1, row - 1), 1, 1, linewidth=1, edgecolor='black', facecolor=color)
            ax.add_patch(rect)
            if name not in ['UNUSED', 'NaN']:
                ax.text(col - 0.5, row - 0.5, name[0], va='center', ha='center')

            if name == target_container:
                ax.text(col - 0.5, row - 0.5, '*', va='center', ha='center', color='red', fontsize=14)

@log_function_call
def heuristic_cost_estimate(current_position, target_position):
    return abs(target_position[0] - current_position[0]) + abs(target_position[1] - current_position[1])

@log_function_call
def a_star_search(initial_state, target_container, ax):
    target_position = None
    for container in initial_state.containers:
        if container['name'] == target_container:
            target_position = container['position']
            break

    if target_position is None:
        print("Target container not found.")
        return None

    frontier = [(0, initial_state)]
    explored = set()

    while frontier:
        _, current_state = heapq.heappop(frontier)

        if current_state.is_goal(target_container):
            return current_state

        explored.add(current_state)

        for neighbor, step_cost in current_state.get_neighbors(target_container):
            if neighbor not in explored:
                heuristic_cost = heuristic_cost_estimate(neighbor.containers[target_container]['position'], target_position)
                total_cost = step_cost + current_state.cost + heuristic_cost
                heapq.heappush(frontier, (total_cost, neighbor))

    return None

@log_function_call
def find_best_location_to_move(blocking_container_coords, initial_state):
    li = []
    li2 = []
    li3 = []
    for row in range(1, initial_state.width + 1, 1):
        left_col = blocking_container_coords[1] - 1
        right_col = blocking_container_coords[1] + 1
        if left_col == 0:
            left_col = 1

        if right_col == initial_state.length + 1:
            right_col = initial_state.length

        for col in range(left_col, right_col + 1):
            if any(c['position'] == (row, col) and (c['name'] == 'UNUSED' or c['name'] == 'NaN') for c in initial_state.containers):
                li.append((row, col))
            elif col != blocking_container_coords[1]:
                li2.append((row, col))

    bc_row, bc_col = blocking_container_coords
    for row, col in li:
        steps = abs(bc_row - row) + abs(bc_col - col)
        li3.append(((row, col), steps))

    selected_location = None
    li3.sort(key=lambda x: x[1])
    for location, steps in li3:
        x, y = location
        x = x - 1
        for cox, coy in li2:
            if x == cox and y == coy:
                selected_location = (x + 1, y)

    return selected_location

@log_function_call
def display_path_with_visualization(state, target_container):
    fig, ax = plt.subplots()
    path = []
    while state:
        path.append(state)
        state = state.parent
    for state in reversed(path):
        state.draw_ship_layout(ax, target_container)
        plt.pause(0.5)
    plt.show()

@log_function_call
def load_and_visualize_process(state, container_name, position):
    fig, ax = plt.subplots()
    state.draw_ship_layout(ax, None)
    plt.pause(1)  
    sorted_containers = sorted(state.containers, key=lambda c: (c['position'][0], c['position'][1]))

    for container in sorted_containers:
        if container['name'] == 'UNUSED':
            continue

        if container['position'] != (1, 1):
            continue

        success, cost = state.load_container(container_name, position, ax)
        if success:
            print(f"Loading container '{container_name}' at position {position}.")
            print(f"Loading cost: {cost} units")
            plt.show()
        else:
            print("Invalid position for loading the container.")
            plt.close()
            return

        plt.pause(0.5)

    print("Loading completed.")
    plt.show()

class ShipContainerGUI:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        set_logging_handler()
        root.geometry("800x600") 
        root.title("Ship Container Management")

        self.welcome_label = tk.Label(root, text=f"Welcome, {self.username}", font=("Arial", 12))
        self.welcome_label.pack()

        self.button_frame = tk.Frame(root) 
        self.button_frame.pack(side=tk.TOP, fill=tk.X)

        self.figure_frame = tk.Frame(root) 
        self.figure_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.ship_width = 8
        self.ship_length = 12
        self.updated_manifest = "manifest_outbound.txt"
        self.state = None
        self.total_steps = 0
        self.ax = None

        self.load_file_button = tk.Button(self.button_frame, text="Load Manifest File", command=lambda: self.load_manifest(first_time=True))
        self.load_file_button.pack(side=tk.LEFT)

        self.comment_button = tk.Button(self.button_frame, text="Add Comment", command=self.log_user_comment)
        self.comment_button.pack(side=tk.LEFT)
        self.logout_button = tk.Button(self.button_frame, text="Logout", command=self.logout)
        self.logout_button.pack(side=tk.RIGHT)
        self.load_button = tk.Button(self.button_frame, text="Load Container", command=self.load_container)
        self.unload_button = tk.Button(self.button_frame, text="Unload Container", command=self.unload_container)
        self.load_button.pack(side=tk.LEFT)
        self.unload_button.pack(side=tk.LEFT)
        self.load_button.pack_forget()
        self.unload_button.pack_forget()

    @log_function_call
    def log_user_comment(self):
        user_comment = simpledialog.askstring("User Comment", "Enter your comment:")
        if user_comment:
            logging.info(f"User comment: {user_comment}")

    @log_function_call
    def logout(self):
        if messagebox.askokcancel("Logout", "Are you sure you want to logout?"):
            self.root.quit()

    @log_function_call
    def load_manifest(self, first_time=False):
        file_path = self.updated_manifest if not first_time else filedialog.askopenfilename()
        if file_path:
            with open(file_path, 'r') as file:
                manifest = file.read()
            containers = parse_manifest(manifest)
            self.state = State(containers, self.ship_width, self.ship_length, self.create_visualization_window)
            self.draw_ship_layout()
            self.load_file_button.pack_forget()
            self.load_button.pack()
            self.unload_button.pack()

    def ask_for_another_operation(self):
        global start_time
        response = messagebox.askyesno("Continue", "Do you want to perform another operation?")
        if response:
            self.reset_gui_and_load_manifest()
        else:
            total_steps_message = f"Total number of steps taken: {self.total_steps}\n\nPlease remember to email the updated outbound manifest file."
            messagebox.showinfo("Operation Complete", total_steps_message)

            end_time = time.time()
            total_time = end_time - start_time
            print(f"Total time taken: {total_time:.2f} seconds")  

            if self.root.winfo_exists():
                self.root.quit()

    def reset_gui_and_load_manifest(self):
        for widget in self.figure_frame.winfo_children():
            widget.destroy()
        if hasattr(self, 'load_button'):
            self.load_button.pack_forget()
        if hasattr(self, 'unload_button'):
            self.unload_button.pack_forget()
        self.load_manifest(first_time=False)

    def create_visualization_window(self):
        new_window = tk.Toplevel(self.root)
        new_window.title("Visualization")
        return new_window

    @log_function_call
    def choose_operation(self):
        self.load_button = tk.Button(self.root, text="Load Container", command=self.load_container)
        self.unload_button = tk.Button(self.root, text="Unload Container", command=self.unload_container)
        self.load_button.pack()
        self.unload_button.pack()

    @log_function_call
    def load_container(self):
        if not self.state:
            print("Load a manifest file first.")
            return
        container_name = simpledialog.askstring("Container Name", "Enter the name of the container to load:")
        if not container_name:
            return

        position_str = simpledialog.askstring("Container Position", "Enter the position to load the container (row, col):")
        if not position_str:
            return

        position = tuple(map(int, position_str.split(',')))

        weight = simpledialog.askinteger("Container Weight", "Enter the weight of the container:")
        if not weight:
            return

        fig, ax = plt.subplots()
        success, steps = self.state.load_container(container_name, position, weight, ax)
        if success:
            self.state.write_manifest(self.updated_manifest)
            self.draw_ship_layout()
        else:
            print("Invalid position for loading the container.")

        plt.close(fig)

        self.total_steps += steps
        self.ask_for_another_operation()

    @log_function_call
    def display_path_with_visualization(self, state, target_container):
        fig, ax = plt.subplots()
        path = []
        while state:
            path.append(state)
            state = state.parent
        for state in reversed(path):
            state.draw_ship_layout(ax, target_container)
            plt.pause(0.5)
        plt.show()

    @log_function_call
    def unload_container(self):
        if not self.state:
            print("Load a manifest file first.")
            return

        is_above, blocking_container, _ = self.state.is_container_above((self.state.width, 1))
        steps = 1

        if is_above:
            selected_location = find_best_location_to_move(blocking_container['position'], self.state)
            if selected_location:
                self.state.move_container_to_position(blocking_container['name'], blocking_container['position'], selected_location, self.ax)
                self.state.write_manifest(self.updated_manifest)
                self.draw_ship_layout()
            else:
                print("No valid location found to move the blocked container.")
                return
            self.state = State(self.state.containers, self.ship_width, self.ship_length, self.create_visualization_window, parent=None, cost=0, last_move=None)
            
        if hasattr(self, 'container_to_unload') and self.container_to_unload:
            main_container = self.container_to_unload
            delattr(self, 'container_to_unload') 
        else:
            main_container = simpledialog.askstring("Main Container", "Enter the name of the main container to unload:")
            if not main_container:
                return
            self.container_to_unload = main_container

        solution_state = a_star_search(self.state, main_container, self.ax)
        if solution_state:
            self.display_path_with_visualization(solution_state, main_container)
            self.state.containers = [c for c in solution_state.containers if c['name'] != main_container]
            self.state.write_manifest(self.updated_manifest)
            self.draw_ship_layout()
            steps = solution_state.cost
            print(f"Unloading container '{main_container}' took {steps} steps.")
            self.total_steps += steps 
            self.ask_for_another_operation()
        else:
            print("No solution found.")

    @log_function_call
    def draw_ship_layout(self):
        if self.state:
            fig, self.ax = plt.subplots()
            self.state.draw_ship_layout(self.ax, None)
            canvas = FigureCanvasTkAgg(fig, master=self.figure_frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack()
            canvas.draw()

@log_function_call
def login_window(root):
    login_win = tk.Toplevel(root)
    login_win.title("Login")
    login_win.geometry("800x400") 

    tk.Label(login_win, text="Welcome to Port Organizer Management System", font=("Arial", 14)).pack()
    tk.Label(login_win, text="Please enter your login details", font=("Arial", 10)).pack(pady=(10, 20))

    tk.Label(login_win, text="Username").pack()
    username_entry = tk.Entry(login_win)
    username_entry.pack()

    tk.Label(login_win, text="Password").pack()
    password_entry = tk.Entry(login_win, show="*")
    password_entry.pack()
    
    def check_login():
        if username_entry.get() == "Praneeth" and password_entry.get() == "":
            username = username_entry.get()
            login_win.destroy()
            root.deiconify()
            app = ShipContainerGUI(root, username)
        else:
            tk.messagebox.showerror("Login failed", "Incorrect username or password")

    submit_button = tk.Button(login_win, text="Login", command=check_login)
    submit_button.pack()

def main():
    global start_time
    start_time = time.time() 
    root = tk.Tk()
    root.title("Ship Container Management")
    root.withdraw()
    login_window(root)
    root.mainloop()

if __name__ == "__main__":
    main()