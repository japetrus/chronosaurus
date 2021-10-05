# Original code from Roger Powell
# Original manuscript ...
# Adapted by JAP for use with Chronosaurus

import sys
import datetime
import numpy as np

defaulth = 1.4             # default h in huber
screen = sys.stdout
#out = open("out.txt", "w") # opening output file
standard = [screen]   # default where print goes

def nmad(e):
    return 1.4826 * np.median(np.absolute(e - np.median(e)))

def siegel(data): # siegel (1982)
    n = data.shape[0];  
    (x, sdx, y, sdy, cor) = np.transpose(data)
    x += 1e-8 * np.random.random(n) # naive breaking of x ties
    med = np.empty(n);  
    for i in range(n):
        col = np.empty(n);  
        for j in range(n):
            if i is not j: col[j] = (y[j] - y[i])/(x[j] - x[i])
        med[i] = np.median(np.delete(col, i)) 
    b = np.median(med)
    return np.array((np.median(y - x * b), b))

# ------------------------------------------------------

def calcage(theta, covtheta = None, method = 1):
# tera-wasserburg: focus on lower intercept
    dc238 = 1.55125e-10; dc235 = 9.8485e-10
    tc = 0; t = t1 = 1500.; tdiff = 1e-4
    (a, b) = theta
    k = 0
    while k < 12 and abs(t - tc) > tdiff:
        tc = t; t = 1/dc238 * np.log(1 + 1/t1)
        t1 = (1/137.8 * (np.exp(dc235 * t) - 1) / (np.exp(dc238 * t) - 1) - a) / b
        k += 1
    if covtheta is None:
        sdage = 0
    else:
        den = b * np.exp(dc238 * t) * dc238 + \
                (-np.exp(dc235 * t) * dc235 + np.exp(dc235 * t + dc238 * t) * dc235 + \
                  np.exp(dc238 * t) * dc238 - np.exp(dc235 * t + dc238 * t) * dc238)/137.8
        jac = [(np.exp(dc238 * t) - 1)/den * (np.exp(dc238 * t) - 1), (np.exp(dc238 * t) - 1)/den]
        sdage = np.sqrt(np.dot(np.dot(jac, covtheta), np.transpose(jac)))/1e6
    return (t/1e6, sdage)

# ------------------------------------------------------

def huber2(data0, h = 1.4):
#   huber line-fitter
    n = data0.shape[0]
    itmax = 2000; mindel = 1e-15; mincond = 1e-12; minsump = 0.01
    (x, sdx, y, sdy, cor) = np.transpose(data0)
    avx = np.dot(x, np.ones(n))/n;  avy = np.dot(y, np.ones(n))/n;
    div = np.array([1/avy, avx/avy])
    data = np.copy(data0)
    (x, sdx, y, sdy, cor) = np.transpose(data)
    x /= avx; sdx /= avx; y /= avy; sdy /= avy; cov = sdx*sdy*cor
    theta = siegel(data);                            
    k = 0; code = 0; deltheta = (1e10, 1e10)
    while k < itmax and ( np.sqrt(np.dot(deltheta,deltheta)) > mindel): 
        k += 1; (a, b) = oldtheta = theta
        e = a + b * x - y;  sde = np.sqrt(b**2*sdx**2 - 2*b*cov + sdy**2)
        r = e/sde
        wh = [1 if abs(rk) < h else np.sqrt(h/abs(rk)) for rk in r]/sde
        xp = x - r * (b*sdx**2 - cov)/sde            # x on the line
        ypp = (y - e - r*(b*cov - sdy**2)/sde)*wh    # W^(1/2)(y'-e): y off the line
        c = np.transpose([wh, xp*wh])                # W^(1/2) X'
        (u, s, v) = np.linalg.svd(c, full_matrices=False)
        if mincond * s[0] > s[1]: code = -1; break   # (nearly) singular matrix
        theta = np.dot(np.dot(np.dot(np.transpose(v), np.diag(1/s)), np.transpose(u)), ypp)
        deltheta = theta - oldtheta   
        print(deltheta)
    if k == itmax: code = 1  # not converged
    pc = np.dot([wh**2, xp*wh**2], e);
    sump = np.sqrt(np.dot(pc, pc));     
    if sump > minsump: code = 2  # not solved the nle
    dpsi = [1 if abs(rk) < h else 0 for rk in r] 
    covtheta = np.linalg.inv(np.dot(np.dot(np.transpose(c), np.diag(dpsi)), c)) / \
        np.array([[div[0]**2, div[0] * div[1]], [div[0] * div[1], div[1]**2]])
    return (code, theta/div, covtheta, sump, k, s[1])

# ------------------------------------------------------

def pr(s, e="\n", printto=standard):
# prints a string
    for pr in printto: print(s, end=e, file=pr)

def recipe(title, data, where = [screen]):
#   prototype calculation driver
    h = defaulth
    (x, sdx, y, sdy, cor) = np.transpose(data)
    n = data.shape[0]
    today = datetime.datetime.now();
    pr("==========================================================\n"+ \
       "running spine.py on "+today.ctime())
    res = huber2(data)
    if res[0] != 0: 
        print("sample "+title+" not calculated")
        return "bad"  
    (a, b) = theta = res[1]
    ucovtheta = res[2]
    (age, sdage) = calcage(theta, ucovtheta)
    e = a + b * x - y
    sde = np.sqrt(b**2 * sdx**2 - 2 * b * sdx * sdy * cor + sdy**2)
    r = e/sde
    s = nmad(r); slim = 1.92 - 0.162 * np.log(10 + n); # print(slim)
    if s < slim:
        pr(("sample "+title+": s = %0.2f"+ ": isochron " + "age = %0.3f +/- %0.3f Ma") % \
           (s, age, 1.96 * sdage), printto = where)
    else:
        pr(("sample "+title+": s = %0.2f"+ ": errorchron " + "age = %0.3f Ma") % \
           (s, age), printto = where)
    return [0, age, sdage, theta]

"""
# ------------------------------------------------------
data = np.loadtxt("data0708.txt", delimiter=",")

print("siegel ", siegel(data))

recipe("0708", data, where=standard); print()

res = huber2(data)
print("huber ", res);  
theta = res[1]; covtheta = res[2]
print(calcage(theta, covtheta)); print()

res = huber2(data, h=100)
print("york ", res);  
theta = res[1]; covtheta = res[2]
print(calcage(theta, covtheta)); print()

print()
out.flush()
out.close()
"""