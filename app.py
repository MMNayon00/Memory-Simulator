# app.py
# --- Imports ---
from flask import Flask, render_template, request, jsonify
import math

# --- Flask App Initialization ---
app = Flask(__name__)

# --- In-memory "database" to store the state of our simulators ---
# This dictionary will hold the state for each memory management type.
# It will be reset every time the server restarts.
memory_state = {}

def initialize_state():
    """Initializes/resets the memory state for all simulators."""
    global memory_state
    memory_state = {
        'contiguous': {
            'memory_size': 1024,
            'memory': [{'start': 0, 'size': 1024, 'status': 'free'}],
            'processes': {},
            'process_id_counter': 0
        },
        'paging': {
            'memory_size': 1024,
            'page_size': 16,
            'frames': [{'status': 'free'}] * (1024 // 16),
            'processes': {},
            'process_id_counter': 0
        },
        'segmentation': {
            'memory_size': 1024,
            'memory': [{'start': 0, 'size': 1024, 'status': 'free'}],
            'processes': {},
            'process_id_counter': 0
        }
    }

# --- Helper Functions ---
def get_process_color(process_id):
    """Assigns a consistent color class based on process ID."""
    colors = [f'process-color-{i}' for i in range(7)]
    return colors[process_id % len(colors)]

def coalesce_memory(memory_map):
    """Merges adjacent free blocks in a memory map."""
    if not memory_map:
        return []
    
    coalesced = []
    current_block = memory_map[0]

    for next_block in memory_map[1:]:
        if current_block['status'] == 'free' and next_block['status'] == 'free':
            current_block['size'] += next_block['size']
        else:
            coalesced.append(current_block)
            current_block = next_block
    coalesced.append(current_block)
    return coalesced

# --- Contiguous Allocation Logic ---
@app.route('/api/contiguous/allocate', methods=['POST'])
def allocate_contiguous():
    data = request.json
    process_size = int(data['processSize'])
    strategy = data['strategy']
    state = memory_state['contiguous']

    free_blocks = [(i, block) for i, block in enumerate(state['memory']) if block['status'] == 'free' and block['size'] >= process_size]

    if not free_blocks:
        return jsonify({'success': False, 'message': 'Not enough memory.'}), 400

    block_to_allocate = None
    block_index = -1

    if strategy == 'firstFit':
        block_index, block_to_allocate = free_blocks[0]
    elif strategy == 'bestFit':
        block_index, block_to_allocate = min(free_blocks, key=lambda item: item[1]['size'])
    elif strategy == 'worstFit':
        block_index, block_to_allocate = max(free_blocks, key=lambda item: item[1]['size'])

    process_id = state['process_id_counter']
    state['processes'][process_id] = {'id': process_id, 'size': process_size, 'start': block_to_allocate['start']}
    
    allocated_block = {'start': block_to_allocate['start'], 'size': process_size, 'status': 'allocated', 'processId': process_id}
    
    remaining_size = block_to_allocate['size'] - process_size
    if remaining_size > 0:
        free_block = {'start': block_to_allocate['start'] + process_size, 'size': remaining_size, 'status': 'free'}
        state['memory'][block_index:block_index+1] = [allocated_block, free_block]
    else:
        state['memory'][block_index] = allocated_block

    state['process_id_counter'] += 1
    return jsonify({'success': True, 'state': state})

@app.route('/api/contiguous/deallocate', methods=['POST'])
def deallocate_contiguous():
    data = request.json
    process_id = int(data['processId'])
    state = memory_state['contiguous']

    if process_id in state['processes']:
        del state['processes'][process_id]
        for i, block in enumerate(state['memory']):
            if block.get('processId') == process_id:
                state['memory'][i] = {'start': block['start'], 'size': block['size'], 'status': 'free'}
                break
        state['memory'] = coalesce_memory(state['memory'])

    return jsonify({'success': True, 'state': state})

@app.route('/api/contiguous/reset', methods=['POST'])
def reset_contiguous():
    data = request.json
    memory_size = int(data.get('memorySize', 1024))
    memory_state['contiguous'] = {
        'memory_size': memory_size,
        'memory': [{'start': 0, 'size': memory_size, 'status': 'free'}],
        'processes': {},
        'process_id_counter': 0
    }
    return jsonify({'success': True, 'state': memory_state['contiguous']})

# --- Paging Logic ---
@app.route('/api/paging/allocate', methods=['POST'])
def allocate_paging():
    data = request.json
    process_size = int(data['processSize'])
    state = memory_state['paging']
    
    num_pages_needed = math.ceil(process_size / state['page_size'])
    free_frame_indices = [i for i, frame in enumerate(state['frames']) if frame['status'] == 'free']

    if num_pages_needed > len(free_frame_indices):
        return jsonify({'success': False, 'message': 'Not enough free frames.'}), 400

    process_id = state['process_id_counter']
    page_table = []
    for i in range(num_pages_needed):
        frame_index = free_frame_indices[i]
        page_table.append({'page': i, 'frame': frame_index})
        state['frames'][frame_index] = {'status': 'allocated', 'processId': process_id, 'pageNum': i}
    
    state['processes'][process_id] = {'id': process_id, 'size': process_size, 'pageTable': page_table}
    state['process_id_counter'] += 1
    
    return jsonify({'success': True, 'state': state})

@app.route('/api/paging/deallocate', methods=['POST'])
def deallocate_paging():
    data = request.json
    process_id = int(data['processId'])
    state = memory_state['paging']
    
    if process_id in state['processes']:
        process = state['processes'][process_id]
        for entry in process['pageTable']:
            state['frames'][entry['frame']] = {'status': 'free'}
        del state['processes'][process_id]

    return jsonify({'success': True, 'state': state})
    
@app.route('/api/paging/reset', methods=['POST'])
def reset_paging():
    data = request.json
    memory_size = int(data.get('memorySize', 1024))
    page_size = int(data.get('pageSize', 16))
    num_frames = memory_size // page_size if page_size > 0 else 0
    
    memory_state['paging'] = {
        'memory_size': memory_size,
        'page_size': page_size,
        'frames': [{'status': 'free'}] * num_frames,
        'processes': {},
        'process_id_counter': 0
    }
    return jsonify({'success': True, 'state': memory_state['paging']})

# --- Segmentation Logic (simplified using best-fit) ---
@app.route('/api/segmentation/allocate', methods=['POST'])
def allocate_segmentation():
    data = request.json
    segment_sizes = [int(s) for s in data['segmentSizes']]
    state = memory_state['segmentation']

    temp_memory = [dict(b) for b in state['memory']]
    allocations = []
    
    for size in segment_sizes:
        free_blocks = [(i, b) for i, b in enumerate(temp_memory) if b['status'] == 'free' and b['size'] >= size]
        if not free_blocks:
            return jsonify({'success': False, 'message': f'Not enough memory for segment of size {size}.'}), 400
        
        # Best-fit for segments
        block_index, block_to_use = min(free_blocks, key=lambda item: item[1]['size'])
        allocations.append({'segSize': size, 'start': block_to_use['start']})
        
        # Update temp memory for next check
        original_block = temp_memory[block_index]
        remaining = original_block['size'] - size
        original_block['size'] = size
        original_block['status'] = 'allocated'
        if remaining > 0:
            temp_memory.insert(block_index + 1, {'start': original_block['start'] + size, 'size': remaining, 'status': 'free'})

    # Commit to actual memory map
    process_id = state['process_id_counter']
    process = {'id': process_id, 'segments': []}
    for i, alloc in enumerate(allocations):
        process['segments'].append({'id': i, 'size': alloc['segSize'], 'base': alloc['start'], 'limit': alloc['segSize']})
    
    state['processes'][process_id] = process
    state['memory'] = temp_memory
    state['process_id_counter'] += 1
    
    return jsonify({'success': True, 'state': state})

@app.route('/api/segmentation/deallocate', methods=['POST'])
def deallocate_segmentation():
    data = request.json
    process_id = int(data['processId'])
    state = memory_state['segmentation']

    if process_id in state['processes']:
        process = state['processes'][process_id]
        del state['processes'][process_id]
        
        for seg in process['segments']:
            for i, block in enumerate(state['memory']):
                if block.get('start') == seg['base'] and block.get('size') == seg['size']:
                    state['memory'][i] = {'start': block['start'], 'size': block['size'], 'status': 'free'}
                    break
        state['memory'] = coalesce_memory(state['memory'])

    return jsonify({'success': True, 'state': state})

@app.route('/api/segmentation/reset', methods=['POST'])
def reset_segmentation():
    data = request.json
    memory_size = int(data.get('memorySize', 1024))
    memory_state['segmentation'] = {
        'memory_size': memory_size,
        'memory': [{'start': 0, 'size': memory_size, 'status': 'free'}],
        'processes': {},
        'process_id_counter': 0
    }
    return jsonify({'success': True, 'state': memory_state['segmentation']})


# --- Main Route to Serve the HTML Page ---
@app.route('/')
def index():
    """Renders the main HTML page."""
    initialize_state() # Reset state on each page load/refresh
    return render_template('index.html')

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)
