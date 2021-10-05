def formatResult(val, unc, sigds = 3):
	from math import log10
	try:
		val_exp = int(log10(abs(val)))
		unc_exp = int(log10(abs(unc)))
	except:
		return ('%g ± %g'%(val, unc), val, unc)
	if unc_exp < 0:
		unc_exp -= 1
	fval = round(val * 10 ** (sigds - 1 - unc_exp)) * 10 ** (unc_exp - sigds + 1)
	func = round(unc * 10 ** (sigds - 1 - unc_exp)) * 10 ** (unc_exp - sigds + 1)
	return ('%g ± %g'%(fval, func), fval, func)


def fitLine(x, sx, y, sy, r, model=1):
    import numpy as np
    from scipy.optimize import leastsq
    from scipy import stats
    from math import sqrt

    wx = sx**-2
    wy = sy**-2

    def fxyz(b, x, wx, y, wy, r):
        z = wx * wy / (b ** 2 * wy + wx - 2.0 * b * r * np.sqrt(wx * wy))
        x_bar = np.sum(z * x) / np.sum(z)
        y_bar = np.sum(z * y) / np.sum(z)
        a = y_bar - b * x_bar
        S = np.sum(z * (y - b * x - a) ** 2)
        return (x_bar, y_bar, z, S)

    def ff(b, x, wx, y, wy, r):
        x_bar, y_bar, z, S = fxyz(b, x, wx, y, wy, r)
        (u, v) = (x - x_bar, y - y_bar)
        A = np.sum(z ** 2 * ((u * v / wx) - (r * u ** 2) / np.sqrt(wx * wy)))
        B = np.sum(z ** 2 * ((u ** 2 / wy) - (v ** 2) / wx))
        C = np.sum(z ** 2 * ((u * v / wy) - (r * v ** 2) / np.sqrt(wx * wy)))
        S = (-B + np.sqrt(B ** 2 + 4 * A * C)) / (2 * A) - b
        return S

    if model == 1 or isinstance(model, str) and model.lower() == 'york':
        m = leastsq(ff, 1.0, args=(x, wx, y, wy, r))[0][0]
        x_bar, y_bar, z, _ = fxyz(m, x, wx, y, wy, r)
        b = y_bar - m*x_bar
        sigma_m = np.sqrt(1.0 / np.sum(z * (x - x_bar) ** 2))
        sigma_b = np.sqrt(1.0 / np.sum(z) + x_bar ** 2 * sigma_m ** 2)
        ww = 1. / (sy**2 + m**2 * sx**2 - 2 * m * r * sx * sy)
        mswd = np.sum(ww * (y - m*x - b)**2)
        P = 1 - stats.chi2.cdf(mswd, len(x)-2)
        mswd /= (len(x) - 2)
    elif model == 2 or isinstance(model, str) and model.lower() == 'ols':
        from numpy import polyfit
        print(f'fitLine with {x} {y}')
        p, cov = polyfit(x, y, 1, cov=True)
        print(p)
        print(cov)
        b = p[1]
        m = p[0]
        x_bar = np.mean(x)
        y_bar = np.mean(y)
        sigma_m = cov[0][0]**0.5
        sigma_b = cov[1][1]**0.5
        mswd = np.sum( (y - (m*x+b))**2 )
        P = 1 - stats.chi2.cdf(mswd, len(x)-2)
        mswd /= (len(x) - 2)
    elif model == 3 or isinstance(model, str) and model.lower() == 'huber':
        from app.thirdparty.spine import huber2
        
        res = huber2(np.array([x, sx, y, sy, r]).transpose())
        if res[0] < 0:
            raise Exception('There was a problem fitting your data.')
        if res[0] > 0:
            print('The fit did not converge.')

        x_bar = np.mean(x)
        y_bar = np.mean(y)
        b = res[1][0]
        m = res[1][1]
        sigma_b = sqrt(res[2][0][0])
        sigma_m = sqrt(res[2][1][1])
        mswd = np.sum( (y - (m*x+b))**2 )
        P = 1 - stats.chi2.cdf(mswd, len(x)-2)
        mswd /= (len(x) - 2)        

    return {
        'x_bar': x_bar,
        'y_bar': y_bar,
        'b': b,
        'm': m,
        'sigma_b': sigma_b,
        'sigma_m': sigma_m,
        'mswd': mswd,
        'prob': P
    }


def weightedMean(x, sd, output=False):
    from scipy.optimize import newton, bisect
    from scipy import stats
    from math import sqrt, log10, floor
    import numpy as np

    w = 1/sd**2
    xbar = np.average(x, weights=w)
    intmean = np.sum(w*x)/np.sum(w)
    intsigmamean = sqrt(1/np.sum(w))
    t = stats.t.ppf(1-0.025, len(x)-1)
    mswd = (1 / (len(x) - 1)) * np.sum( (x-xbar)**2/sd**2)
    wmswd = (np.sum(w) / ( (np.sum(w)**2) - np.sum(w**2) ) ) * np.sum(w * (x - xbar)**2 / sd**2)
    prob = 1 - stats.f.cdf(mswd, len(x)-1, 1000000000)
    intmeanerr95 = t*intsigmamean*sqrt(mswd)
    if prob >= 0.3:
        intmeanerr95 = intsigmamean * 1.96


    def f(ev):
        wf = 1/(ev + sd**2)
        sumw = np.sum(wf)
        sumxw = np.sum(x*wf)

        xbarf = sumxw/sumw
        resid = x - xbarf
        sumw2resid2 = np.sum( (wf*resid)**2 )
        return sumw2resid2 - sumw


    if output:
        print('Weighted Average Report:')
        print('################################################')
        print('Wtd by assigned/internal errors only')
        print('    %f +/- %f'%(xbar, 2*intsigmamean))
        print('    %f +/- %f'%(xbar, intmeanerr95))
        print('    MSWD = %f'%(mswd))
        print('    Probability of fit = %f'%(prob))
        print('------------------------------------------------')

    ext_xbar = xbar
    ext_err = intmeanerr95
    extsigma = 0
    if mswd > 1:
        if output:
            print('Wtd by assigned errors + constant external error')
        try:
            #extvar = bisect(f, 0, 10*np.var(x))
            extvar = newton(f, np.var(x))
            wf = 1/(extvar + sd**2)
            xbarfsigma = sqrt(abs(1/np.sum(wf)))
            xbarf = np.sum(x*wf)/np.sum(wf)
            extsigma = sqrt(extvar)
            extmeanerr95 = stats.t.ppf(1-0.025, 2*len(x) - 2)*xbarfsigma
            if output:
                print('    %f +/- %f'%(xbarf, extmeanerr95))
                print('    External 2-sigma err req\'d (each pt) = %f'%(extsigma*2))
            ext_xbar = xbarf
            ext_err = extmeanerr95
        except Exception as e:
            # If root finding failed and large MSWD (same as IsoPlot)
            print(e)
            if mswd > 4:
                extsigma = np.std(x, ddof=1)
                extmeanerr95 = stats.t.ppf(1-0.025, len(x)-1)*extsigma/sqrt(len(x))
                if output:
                    print('    %f +/- %f'%(np.mean(x), extmeanerr95))
                    print('    External 2-sigma err req\'d (each pt) = %f'%(extsigma*2))
                ext_xbar = np.mean(x)
                ext_err = extmeanerr95

    if output:
        print('\n')

    return {
        'internal': (xbar, intmeanerr95),
        'external': (ext_xbar, ext_err),
        'mswd': mswd,
        'prob': prob,
        'extra': extsigma
    }


def weightedMean2D(x, sx, y, sy, r):
    import numpy as np
    from scipy import stats

    N = len(x)
    covxy = r * sx * sy
    o11 = sy ** 2 / ((sx ** 2) * (sy ** 2) - covxy ** 2)
    o22 = sx ** 2 / ((sx ** 2) * (sy ** 2) - covxy ** 2)
    o12 = -covxy / ((sx ** 2) * (sy ** 2) - covxy ** 2)
    x_bar = (
        np.sum(o22) * np.sum(x * o11 + y * o12)
        - np.sum(o12) * np.sum(y * o22 + x * o12)
    ) / (np.sum(o11) * np.sum(o22) - np.sum(o12) ** 2)
    y_bar = (
        np.sum(o11) * np.sum(y * o22 + x * o12)
        - np.sum(o12) * np.sum(x * o11 + y * o12)
    ) / (np.sum(o11) * np.sum(o22) - np.sum(o12) ** 2)

    (Rx, Ry) = (x - x_bar, y - y_bar)
    S = np.sum(((Rx ** 2.0) * o11) + ((Ry ** 2.0) * o22) + (2.0 * Rx * Ry * o12))
    mswd = S / (2 * N - 2)
    P = 1 - stats.chi2.cdf(S, 2*N - 2)
    sigma_x_bar = np.sqrt(np.sum(o22) / (np.sum(o11) * np.sum(o22) - np.sum(o12) ** 2))
    sigma_y_bar = np.sqrt(np.sum(o11) / (np.sum(o11) * np.sum(o22) - np.sum(o12) ** 2))
    cov_xy_bar = -np.sum(o12) / (np.sum(o11) * np.sum(o22) - np.sum(o12) ** 2)
    rho_xy_bar = cov_xy_bar / (sigma_x_bar * sigma_y_bar)
    return {
        'x_bar': x_bar,
        'y_bar': y_bar,
        'sigma_x_bar': sigma_x_bar,
        'sigma_y_bar': sigma_y_bar,
        'cov_xy_bar': cov_xy_bar,
        'rho_xy_bar': rho_xy_bar,
        'mswd': mswd,
        'prob': P,
        'n': N
    }

def intersection(x1, y1, x2, y2):
    import numpy as np

    x1 = np.asarray(x1)
    x2 = np.asarray(x2)
    y1 = np.asarray(y1)
    y2 = np.asarray(y2)

    def _rect_inter_inner(x1, x2):
        n1 = x1.shape[0]-1
        n2 = x2.shape[0]-1
        X1 = np.c_[x1[:-1], x1[1:]]
        X2 = np.c_[x2[:-1], x2[1:]]
        S1 = np.tile(X1.min(axis=1), (n2, 1)).T
        S2 = np.tile(X2.max(axis=1), (n1, 1))
        S3 = np.tile(X1.max(axis=1), (n2, 1)).T
        S4 = np.tile(X2.min(axis=1), (n1, 1))
        return S1, S2, S3, S4

    def _rectangle_intersection_(x1, y1, x2, y2):
        S1, S2, S3, S4 = _rect_inter_inner(x1, x2)
        S5, S6, S7, S8 = _rect_inter_inner(y1, y2)

        C1 = np.less_equal(S1, S2)
        C2 = np.greater_equal(S3, S4)
        C3 = np.less_equal(S5, S6)
        C4 = np.greater_equal(S7, S8)

        ii, jj = np.nonzero(C1 & C2 & C3 & C4)
        return ii, jj

    ii, jj = _rectangle_intersection_(x1, y1, x2, y2)
    n = len(ii)

    dxy1 = np.diff(np.c_[x1, y1], axis=0)
    dxy2 = np.diff(np.c_[x2, y2], axis=0)

    T = np.zeros((4, n))
    AA = np.zeros((4, 4, n))
    AA[0:2, 2, :] = -1
    AA[2:4, 3, :] = -1
    AA[0::2, 0, :] = dxy1[ii, :].T
    AA[1::2, 1, :] = dxy2[jj, :].T

    BB = np.zeros((4, n))
    BB[0, :] = -x1[ii].ravel()
    BB[1, :] = -x2[jj].ravel()
    BB[2, :] = -y1[ii].ravel()
    BB[3, :] = -y2[jj].ravel()

    for i in range(n):
        try:
            T[:, i] = np.linalg.solve(AA[:, :, i], BB[:, i])
        except:
            T[:, i] = np.Inf

    in_range = (T[0, :] >= 0) & (T[1, :] >= 0) & (
        T[0, :] <= 1) & (T[1, :] <= 1)

    xy0 = T[2:, in_range]
    xy0 = xy0.T
    return xy0[:, 0], xy0[:, 1]

def concordiaIntercepts(m, b, tw):
    import numpy as np
    l235U = 9.8485 * 10 ** (-10)
    l238U = 1.55125 * 10 ** (-10)
    U85r = 137.818

    def concSlope(t, tw):
        if tw:
            A = (1./U85r)
            B = l235U
            C = l238U
            dydt = (A*B*np.exp(B*t))/(np.exp(C*t) - 1) - (A*C*(np.exp(B*t) - 1)*np.exp(C*t))/(np.exp(C*t) - 1)**2
            dxdt = -l238U*np.exp(l238U*t)/(np.exp(l238U*t)-1)**2
            cs = dydt/dxdt
        else:
            Eterm = (l238U - l235U)*t
            cs = l238U * np.exp(Eterm)/l235U

        return cs

    def concX(t, tw):
        if tw:
            return 1.0/(np.exp(l238U * t) - 1)
        else:
            return np.exp(l235U*t) - 1

    def concY(t, tw):
        if tw:
            return (1.0/U85r)*(np.exp(l235U * t) - 1)/(np.exp(l238U * t) - 1)
        else:
            return np.exp(l238U*t) - 1

    def concXage(X, tw):
        if tw:
            return np.log(1/X + 1)/l238U
        else:
            return np.log(X+1)/l235U

    intercepts = []
    sts = [-500e6, 5500e6]

    for st in sts:
        tt = st
        delta = np.inf
        itn = 0
        while delta > 0.01 and itn < 100:
            cs = concSlope(tt, tw)
            numer = b + cs*concX(tt, tw) - concY(tt, tw)
            denom = cs - m
            X = numer/denom
            t = concXage(X, tw)
            delta = abs(t - tt)
            itn += 1
            tt = t
        intercepts.append(tt/1e6)
    return intercepts

def concordiaAge(x, sx, y, sy, r, tw=False):
    from scipy.optimize import leastsq
    from scipy import stats
    import numpy as np

    l235U = 9.8485 * 10 ** (-10)
    l238U = 1.55125 * 10 ** (-10)
    U85r = 137.818

    # Conventional concordia curve by Ludwig (1998)
    def FitFuncConv(t, x, y, sigma_x, sigma_y, rho_xy):
        A = (x - (np.exp(l235U * t) - 1)) / sigma_x
        B = (y - (np.exp(l238U * t) - 1)) / sigma_y
        S = np.sum((A ** 2 + B ** 2 - 2 * A * B * rho_xy) / (1 - rho_xy ** 2))
        return S

    # Terra-Wasserburg concordia curve by Ludwig (1998)
    def FitFuncTW(t, x, y, sigma_x, sigma_y, rho_xy):
        A = (x - 1 / (np.exp(l238U * t) - 1)) / sigma_x
        B = (y - (1 / U85r) * (np.exp(l235U * t) - 1) / (np.exp(l238U * t) - 1)) / sigma_y
        S = np.sum((A ** 2 + B ** 2 - 2 * A * B * rho_xy) / (1 - rho_xy ** 2))
        return S

    Tinit = 1e6
    conf = 0.95
    caFunc = FitFuncTW if tw else FitFuncConv

    twm = weightedMean2D(x, sx, y, sy, r)
    X_bar = twm['x_bar']
    Y_bar = twm['y_bar']
    MSWD_bar = twm['mswd']
    sigma_X_bar = twm['sigma_x_bar']
    sigma_Y_bar = twm['sigma_y_bar']
    cov_XY_bar = twm['cov_xy_bar']
    rho_XY_bar = twm['rho_xy_bar']

    T_leastsq = leastsq(
        caFunc, Tinit, args=(X_bar, Y_bar, sigma_X_bar, sigma_Y_bar, rho_XY_bar)
    )[0][0]
    # eq(3)
    oi = np.linalg.inv([[sigma_X_bar ** 2, cov_XY_bar], [cov_XY_bar, sigma_Y_bar ** 2]])

    if tw:
        A = -l238U * np.exp(l238U * T_leastsq) / (np.exp(l238U * T_leastsq) - 1) ** 2
        B = (
            1
            / U85r
            * (
                l235U * np.exp(l235U * T_leastsq) * (np.exp(l238U * T_leastsq) - 1)
                - l238U * np.exp(l238U * T_leastsq) * (np.exp(l235U * T_leastsq) - 1)
            )
            / (np.exp(l238U * T_leastsq) - 1) ** 2
        )
        # eq(13)
        QQ = (A ** 2 * oi[0][0] + B ** 2 * oi[1][1] + 2 * A * B * oi[0][1]) ** (-1)
    else:
        # eq(14)
        Q235 = l235U * np.exp(l235U * T_leastsq)
        Q238 = l238U * np.exp(l238U * T_leastsq)
        # eq(13)
        QQ = (Q235 ** 2 * oi[0][0] + Q238 ** 2 * oi[1][1] + 2 * Q235 * Q238 * oi[0][1]) ** (
            -1
        )

    T_1sigma = np.sqrt(QQ)
    T_sigma = stats.norm.ppf(conf + (1 - conf) / 2.0) * T_1sigma
    S_bar = caFunc(T_leastsq, X_bar, Y_bar, sigma_X_bar, sigma_Y_bar, rho_XY_bar)
    #S = FitFuncConv(T_leastsq, x, y, sx, sy, r)
    S = twm['mswd']*(2*len(x)-2)

    df_concordance = 1
    df_equivalence = 2 * len(x) - 2
    df_combined = df_concordance + df_equivalence
    MSWD_concordance = S_bar / df_concordance
    MSWD_equivalence = S / df_equivalence
    MSWD_combined = (S_bar + S) / df_combined
    P_value_eq = 1 - stats.chi2.cdf(S, df_equivalence)
    P_value_comb = 1 - stats.chi2.cdf(S_bar + S, df_combined)
    P_value_conc = 1 - stats.chi2.cdf(S_bar, df_concordance)

    return {
        't': T_leastsq/1e6,
        'sigma_t': T_sigma/1e6,
        'T_1sigma': T_1sigma/1e6,
        'mswd_conc': MSWD_concordance,
        'mswd_equiv': MSWD_equivalence,
        'mswd_comb': MSWD_combined,
        'prob_conc': P_value_conc,
        'prob_equiv': P_value_eq,
        'prob_comb': P_value_comb,
        'wm': twm
    }

def discordiaAge(x, sx, y, sy, r, tw=False, nc=500, nl=100, model=1):
    import numpy as np
    from scipy import stats
    l235U = 9.8485 * 10 ** (-10)
    l238U = 1.55125 * 10 ** (-10)
    U85r = 137.818

    def SIsigma(x, x_bar, y_bar, b, sigma_a, sigma_b, conf=0.95):
        sigma_a2 = stats.norm.ppf(conf + (1 - conf) / 2.0) * sigma_a
        sigma_b2 = stats.norm.ppf(conf + (1 - conf) / 2.0) * sigma_b
        sigma2 = np.sqrt(sigma_a2 ** 2.0 + sigma_b2 ** 2.0 * x * (x - 2.0 * x_bar))
        return sigma2

    def ages(cx, cy, lx, ly, ageForX):
        iva = intersection(cx, cy, lx, ly)
        aa = []
        for i, iv in enumerate(iva[0]):
            da = ageForX(iv)
            aa.append(da)
        return aa

    fit = fitLine(x, sx, y, sy, r, model=model)
    #print(fit)
    t = np.linspace(-5e9, 5e9, num=nc)
    if tw:
        cx = 1.0/(np.exp(l238U * t) - 1)
        cy = (1.0/U85r)*(np.exp(l235U * t) - 1)/(np.exp(l238U * t) - 1)
    else:
        cx = np.exp(l235U * t) - 1
        cy = np.exp(l238U * t) - 1

    xx = np.linspace(-50, 150, num=nl)
    yy = fit['m']*xx + fit['b']
    ss = SIsigma(xx, fit['x_bar'], fit['y_bar'], fit['m'], fit['sigma_b'], fit['sigma_m'])
    yp = fit['m']*xx + fit['b'] + ss
    ym = fit['m']*xx + fit['b'] - ss

    if tw:
        a4x = lambda x: 1e-6*np.log(1/x + 1)/l238U
    else:
        a4x = lambda x: 1e-6*np.log(x + 1)/l235U

    #an = ages(cx, cy, xx, yy, a4x)
    #ap = ages(cx, cy, xx, yp, a4x)
    #am = ages(cx, cy, xx, ym, a4x)
    an = concordiaIntercepts(fit['m'], fit['b'], tw)
    ap = concordiaIntercepts(fit['m']-2*fit['sigma_m'], fit['b'] + 2*fit['sigma_b'], tw)
    am = concordiaIntercepts(fit['m']+2*fit['sigma_m'], fit['b'] - 2*fit['sigma_b'], tw)

    #print(an)
    #print(ap)
    #print(am)

    tc = a4x(fit['x_bar'])

    #print(tc)

    def padAges(a, tc):
        if len(a) == 0:
            return np.array([0, np.inf])
        elif len(a) == 1 and a > tc:
            return np.array([0, a[0]])
        elif len(a) == 1 and a < tc:
            return np.array([a[0], np.inf])
        elif len(a) > 2:
            return np.array([a[-2], a[-1]])
        return a


    aa = np.array( [[0, np.inf]]*3 )
    aa[0, :] = padAges(an, tc)
    aa[1, :] = padAges(ap, tc)
    aa[2, :] = padAges(am, tc)
    aa = np.sort(aa, axis=0)    

    return {
        'upper': aa[1][1],
        'upper plus': aa[2][1],
        'upper minus': aa[0][1],
        'upper 95 conf': abs(aa[0][1] - aa[2][1])/2,
        'lower': aa[1][0],
        'lower 95 conf': abs(aa[0][0] - aa[2][0])/2,
        'lower plus': aa[2][0],
        'lower minus': aa[0][0],
        'fit': fit,
        'CI_bands': {'x': xx, 'yp': yp, 'ym': ym}
    }

