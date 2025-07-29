# Memory Management Simulator

An interactive web-based simulator designed to visualize and explain fundamental operating system memory management algorithms. This tool provides a hands-on approach to understanding how different strategies handle memory allocation and fragmentation.



## ✨ Features

* **Contiguous Allocation Simulation**:
    * **First Fit**: Allocates the first free memory block that is large enough.
    * **Best Fit**: Allocates the smallest free memory block that is large enough, minimizing wasted space.
    * **Worst Fit**: Allocates the largest free memory block, leaving the largest leftover fragment.
* **Paging Simulation**:
    * Divides logical memory into fixed-size pages and physical memory into frames.
    * Visualizes how pages are mapped to non-contiguous frames.
    * Displays page tables for each process and calculates internal fragmentation.
* **Segmentation Simulation**:
    * Models memory allocation where a process is divided into logical segments (e.g., code, data, stack).
    * Shows how variable-sized segments are placed into memory.
    * Displays segment tables for each process.
* **Interactive Interface**:
    * Add processes of varying sizes.
    * Deallocate any process to free up memory.
    * Reset the simulation at any time.
* **Real-time Visualization**:
    * A dynamic memory bar shows allocated partitions and free holes.
    * Process lists and memory tables update instantly.

---

## 🛠️ Tech Stack

* **Backend**: Python with Flask
* **Frontend**: HTML, CSS, and vanilla JavaScript
* **Styling**: Tailwind CSS

---

## 🚀 Setup and Installation

Follow these steps to run the simulator on your local machine.

**1. Organize your project files:**
For Flask to work correctly, you must place your files in the following folder structure:

```
.
├── static/
│   └── style.css
├── templates/
│   └── index.html
└── app.py
```

---

## ⚙️ How It Works

The application uses a client-server model:

* **Flask Backend (`app.py`)**: Acts as an API server. It maintains the state of the memory, performs all the allocation/deallocation calculations when it receives a request, and sends the updated state back to the client.
* **Frontend (`index.html`)**: The user interface runs in the browser. When a user performs an action (like clicking "Add Process"), the JavaScript in the browser sends a `POST` request to the Flask backend. When the backend responds, the JavaScript dynamically updates the HTML to visualize the new memory state without needing to reload the page.

---

