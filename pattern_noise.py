import math
def distributive(list_):
    elements = []
    for i in list_:
        if i not in elements:
            elements.append(i)

    n_elements = len(elements)
    n = len(list_)
    scatter_elements = []
    for i in range(n):
        current_element = elements[i % n_elements]
        scatter_elements.append(current_element)

    return scatter_elements

    
    
def sumative(list):
    output = 0
    for i in list:
        output = output + i
    return output
def create_pattern(value, reacher):
    divider = value / reacher
    #print(divider)
    if divider.is_integer(): 
    
        pattern = [int(divider)] * reacher
        pattern = distributive(pattern)
        sum = sumative(pattern)
        diference = sum - value
        pattern[len(pattern)-1] -= diference
        return pattern
    else:
        divider_floor = math.floor(divider)
        divider_ceil = math.ceil(divider)
        pattern = []
        remainder = value % reacher
        for i in range(reacher):
            if i < remainder:
                pattern.append(divider_ceil)
            else:
                pattern.append(divider_floor)
        pattern = distributive(pattern)
        sum = sumative(pattern)
        diference = sum - value
        pattern[len(pattern)-1] -= diference
        return pattern


def inside_range(value,reach,tolerance):
    if ((value >= (reach-tolerance)) and (value <= (reach+tolerance))):
        return True
    else:
        return False
def incolor(x,y,t):
    r = inside_range(x[0],y[0],t)
    g = inside_range(x[1],y[1],t)
    b = inside_range(x[2],y[2],t)
    a = inside_range(x[3],y[3],t)
    return r and g and b and a
def identify_color(colors,color,t):
    output = False
    index = -1
    if (len(colors) < 1):
        return output, index
    else:
        for c in range(len(colors)):
            isIn_Color = incolor(colors[c],color,t)
            if (isIn_Color):
                output = True
                index = c
    return output, index
    
    
def square_value(value, size):
    y = math.floor(value/size)
    x = value-(y*size)
    return x,y
