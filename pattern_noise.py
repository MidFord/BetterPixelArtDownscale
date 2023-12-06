import math
def distributive(lista):
    elementos = []
    for i in lista:
        if i not in elementos:
            elementos.append(i)

    n_elementos = len(elementos)
    n = len(lista)
    elementos_distribuidos = []
    for i in range(n):
        elemento_actual = elementos[i % n_elementos]
        elementos_distribuidos.append(elemento_actual)

    return elementos_distribuidos

    
    
def sumative(list):
    output = 0
    for i in list:
        output = output + i
#    print(output)
    return output
def create_pattern(value, reacher):
    divider = value / reacher
    print(divider)
    if divider.is_integer(): 
    
        pattern = [int(divider)] * reacher
        pattern = distributive(pattern)
        sum = sumative(pattern)
        diference = sum - value
#        print(diference,value)
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
#        print(diference,value)
        pattern[len(pattern)-1] -= diference
        return pattern
        
        
#print(create_pattern(100, 8))
#print(create_pattern(24, 16))
#print(create_pattern(24, 12))
#print(create_pattern(24, 10))

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
#print(inside_range(123,128,5))
#print(True and False)