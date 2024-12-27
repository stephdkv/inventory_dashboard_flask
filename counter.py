global_counter = {"value": 1}

def get_next_counter_value():
    global global_counter
    global_counter["value"] += 1
    return global_counter["value"]