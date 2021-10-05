import inspect

class System(object):
    pass

class UPb(System):
    name = 'U-(Th)-Pb'

    Pb206_U238 = '²⁰⁶Pb/²³⁸U'
    Pb206_U238_err = '²⁰⁶Pb/²³⁸U error'
    Pb206_U238_age = '²⁰⁶Pb/²³⁸U age'
    Pb206_U238_age_err = '²⁰⁶Pb/²³⁸U age error'

    Pb207_U235 = '²⁰⁷Pb/²³⁵U'
    Pb207_U235_err = '²⁰⁷Pb/²³⁵U error'
    Pb207_U235_age = '²⁰⁷Pb/²³⁵U age'
    Pb207_U235_age_err = '²⁰⁷Pb/²³⁵U age error'

    Wetherill_corr = '²⁰⁶Pb/²³⁸U vs ²⁰⁷Pb/²³⁵U error correlation'

    Pb207_Pb206 = '²⁰⁷Pb/²⁰⁶Pb'
    Pb207_Pb206_err = '²⁰⁷Pb/²⁰⁶Pb error'
    Pb207_Pb206_age = '²⁰⁷Pb/²⁰⁶Pb age'
    Pb207_Pb206_age_err = '²⁰⁷Pb/²⁰⁶Pb age error'

    U238_Pb206 = '²³⁸U/²⁰⁶Pb'
    U238_Pb206_err = '²³⁸U/²⁰⁶Pb error'

    TW_corr = '²³⁸U/²⁰⁶Pb vs ²⁰⁷Pb/²⁰⁶Pb error correlation'

    Pb208_Th232 = '²⁰⁸Pb/²³²Th'
    Pb208_Th232_err = '²⁰⁸Pb/²³²Th error'
    Pb208_Th232_age = '²⁰⁸Pb/²³²Th age'
    Pb208_Th232_age_err = '²⁰⁸Pb/²³²Th age error'

class UTh(System):
    name = 'U-Th'
    Th232_U238 = '²³²Th/²³⁸U'
    Th232_U238_err = '²³²Th/²³⁸U error'
    U234_U238 = '²³⁴U/²³⁸U'
    U234_U238_err = '²³⁴U/²³⁸U error'
    Th230_U238 = '²³⁰Th/²³⁸U'
    Th230_U238_err = '²³⁰Th/²³⁸U error'
    U234_U238_Th230_U238_corr = '²³⁴U/²³⁸U vs ²³⁰Th/²³⁸U error correlation'
    Th232_U238_U234_U238_corr = '²³²Th/²³⁸U vs ²³⁴U/²³⁸U error correlation'
    Th232_U238_Th230_U238_corr = '²³²Th/²³⁸U vs ²³⁰Th/²³⁸U error correlation'

class RbSr(System):
    name = 'Rb-Sr'
    Sr87_Sr86 = '⁸⁷Sr/⁸⁶Sr'
    Sr87_Sr86_err = '⁸⁷Sr/⁸⁶Sr error'
    Rb87_Sr86 = '⁸⁷Rb/⁸⁶Sr'
    Rb87_Sr86_err = '⁸⁷Rb/⁸⁶Sr error'
    RbConc = 'Rb concentration'
    RbConc_err = 'Rb concentration error'
    SrConc = 'Sr concentration'
    SrConc_err = 'Sr concentration error'

class ReOs(System):
    name = 'Re-Os'

class ArAr(System):
    name = 'Ar-Ar'
    Ar39_Ar40 = '³⁹Ar/⁴⁰Ar'
    Ar39_Ar40_err = '³⁹Ar/⁴⁰Ar error'
    Ar36_Ar40 = '³⁶Ar/⁴⁰Ar'
    Ar36_Ar40_err = '³⁶Ar/⁴⁰Ar error'
    Ar39_Ar36 = '³⁹Ar/³⁶Ar'
    Ar39_Ar36_err = '³⁹Ar/³⁶Ar error'
    ArAmount = 'Amount of ³⁹Ar'

class SmNd(System):
    name = 'Sm-Nd'
    Sm147_Nd144 = '¹⁴⁷Sm/¹⁴⁴Nd'
    Sm147_Nd144_err = '¹⁴⁷Sm/¹⁴⁴Nd error'
    Nd143_Nd144 = '¹⁴³Nd/¹⁴⁴Nd'
    Nd143_Nd144_err = '¹⁴³Nd/¹⁴⁴Nd error'

class LuHf(System):
    name = 'Lu-Hf'
    Lu176_Hf177 = '¹⁷⁶Lu/¹⁷⁷Hf'
    Lu176_Hf177_err = '¹⁷⁶Lu/¹⁷⁷Hf error'
    Hf176_Hf177 = '¹⁷⁶Hf/¹⁷⁷Hf'
    Hf176_Hf177_err = '¹⁷⁶Hf/¹⁷⁷Hf error'    

systems = [UPb, UTh, RbSr, ReOs, ArAr, SmNd, LuHf]

class Columns(object):
    namesForSystem = {}
    titlesForSystem = {}
    pass

for system in systems:
    systemColumns = [v[0] for v in inspect.getmembers(system) if not inspect.isfunction(v[1]) and not v[0].startswith('__') and v[0] not in ['name']]
    Columns.namesForSystem[system.name] = systemColumns
    Columns.titlesForSystem[system.name] = [getattr(system, sc) for sc in systemColumns]

    for column in systemColumns:
        setattr(Columns, f'{column}', getattr(system, column))
        

