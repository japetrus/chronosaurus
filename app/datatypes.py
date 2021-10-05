


class DataTypes(object):
    U_Pb = 'U-(Th)-Pb'
    Rb_Sr = 'Rb-Sr'
    Re_Os = 'Re-Os'
    Ar_Ar = 'Ar-Ar'
    Sm_Nd = 'Sm-Nd'
    Lu_Hf = 'Lu-Hf'
    U_Th = 'U-Th'
    Other = 'Other'

class ColumnTypes(object):
    Value = 'Value'
    Error = 'Error'
    ErrorCorrelation = 'ErrorCorrelation'
    All = 'All'




class Columns:

    Pb206_U238 = '²⁰⁶Pb/²³⁸U'
    Pb206_U238_err = '²⁰⁶Pb/²³⁸U error'
    Pb206_U238_age = '²⁰⁶Pb/²³⁸U age'
    Pb206_U238_age_err = '²⁰⁶Pb/²³⁸U age error'

    Pb207_U235 = '²⁰⁷Pb/²³⁵U'
    Pb207_U235_err = '²⁰⁷Pb/²³⁵U error'
    Pb207_U235_age = '²⁰⁷Pb/²³⁵U age'
    Pb207_U235_age_err = '²⁰⁷Pb/²³⁵U age error'

    WetherillErrorCorrelation = '²⁰⁶Pb/²³⁸U vs ²⁰⁷Pb/²³⁵U error correlation'

    Pb207_Pb206 = '²⁰⁷Pb/²⁰⁶Pb'
    Pb207_Pb206_err = '²⁰⁷Pb/²⁰⁶Pb error'
    Pb207_Pb206_age = '²⁰⁷Pb/²⁰⁶Pb age'
    Pb207_Pb206_age_err = '²⁰⁷Pb/²⁰⁶Pb age error'

    U238_Pb206 = '²³⁸U/²⁰⁶Pb'
    U238_Pb206_err = '²³⁸U/²⁰⁶Pb error'

    TWErrorCorrelation = '²³⁸U/²⁰⁶Pb vs ²⁰⁷Pb/²⁰⁶Pb error correlation'

    Pb208_Th232 = '²⁰⁸Pb/²³²Th'
    Pb208_Th232_err = '²⁰⁸Pb/²³²Th error'
    Pb208_Th232_age = '²⁰⁸Pb/²³²Th age'
    Pb208_Th232_age_err = '²⁰⁸Pb/²³²Th age error'

    # U-Th
    Th232_U238 = '²³²Th/²³⁸U'
    Th232_U238_err = '²³²Th/²³⁸U error'
    U234_U238 = '²³⁴U/²³⁸U'
    U234_U238_err = '²³⁴U/²³⁸U error'
    Th230_U238 = '²³⁰Th/²³⁸U'
    Th230_U238_err = '²³⁰Th/²³⁸U error'
    U234_U238_Th230_U238_corr = '²³⁴U/²³⁸U vs ²³⁰Th/²³⁸U error correlation'
    Th232_U238_U234_U238_corr = '²³²Th/²³⁸U vs ²³⁴U/²³⁸U error correlation'
    Th232_U238_Th230_U238_corr = '²³²Th/²³⁸U vs ²³⁰Th/²³⁸U error correlation'


    # Rb-Sr
    Sr87_Sr86 = '⁸⁷Sr/⁸⁶Sr'
    Sr87_Sr86_err = '⁸⁷Sr/⁸⁶Sr error'
    Rb87_Sr86 = '⁸⁷Rb/⁸⁶Sr'
    Rb87_Sr86_err = '⁸⁷Rb/⁸⁶Sr error'
    RbConc = 'Rb concentration'
    RbConc_err = 'Rb concentration error'
    SrConc = 'Sr concentration'
    SrConc_err = 'Sr concentration error'

    # Sm-Nd
    Sm147_Nd144 = '¹⁴⁷Sm/¹⁴⁴Nd'
    Sm147_Nd144_err = '¹⁴⁷Sm/¹⁴⁴Nd error'
    Nd143_Nd144 = '¹⁴³Nd/¹⁴⁴Nd'
    Nd143_Nd144_err = '¹⁴³Nd/¹⁴⁴Nd error'

    # Lu-Hf
    Lu176_Hf177 = '¹⁷⁶Lu/¹⁷⁷Hf'
    Lu176_Hf177_err = '¹⁷⁶Lu/¹⁷⁷Hf error'
    Hf176_Hf177 = '¹⁷⁶Hf/¹⁷⁷Hf'
    Hf176_Hf177_err = '¹⁷⁶Hf/¹⁷⁷Hf error'

    # Ar-Ar
    Ar39_Ar40 = '³⁹Ar/⁴⁰Ar'
    Ar39_Ar40_err = '³⁹Ar/⁴⁰Ar error'
    Ar36_Ar40 = '³⁶Ar/⁴⁰Ar'
    Ar36_Ar40_err = '³⁶Ar/⁴⁰Ar error'
    Ar39_Ar36 = '³⁹Ar/³⁶Ar'
    Ar39_Ar36_err = '³⁹Ar/³⁶Ar error'
    ArAmount = 'Amount of ³⁹Ar'

    column_list = [Pb206_U238, Pb206_U238_err,
                   Pb207_U235, Pb207_U235_err,
                   Pb207_Pb206, Pb207_Pb206_err,
                   WetherillErrorCorrelation,
                   U238_Pb206, U238_Pb206_err,
                   TWErrorCorrelation,
                   Sr87_Sr86, Sr87_Sr86_err,
                   Rb87_Sr86, Rb87_Sr86_err,
                   SrConc, SrConc_err,
                   RbConc, RbConc_err,
                   Sm147_Nd144, Sm147_Nd144_err,
                   Nd143_Nd144, Nd143_Nd144_err,
                   Lu176_Hf177, Lu176_Hf177_err,
                   Hf176_Hf177, Hf176_Hf177_err,
                   Ar39_Ar40, Ar39_Ar40_err, ArAmount,
                   Ar36_Ar40, Ar36_Ar40_err,
                   Ar39_Ar36, Ar39_Ar36_err,
                   Th232_U238, Th232_U238_err,
                   U234_U238, U234_U238_err,
                   Th230_U238, Th230_U238_err,
                   U234_U238_Th230_U238_corr,
                   Th232_U238_Th230_U238_corr,
                   Th232_U238_U234_U238_corr]

    value_list = [Pb206_U238,
                  Pb207_U235,
                  Pb207_Pb206,
                  U238_Pb206,
                  Sr87_Sr86,
                  Rb87_Sr86,
                  SrConc,
                  RbConc,
                  Sm147_Nd144,
                  Nd143_Nd144,
                  Lu176_Hf177,
                  Hf176_Hf177,
                  Ar39_Ar40,
                  Ar36_Ar40,
                  Ar39_Ar36,
                  Th232_U238,
                  U234_U238,
                  Th230_U238
                  ]

    error_list = [Pb206_U238_err,
                  Pb207_U235_err,
                  Pb207_Pb206_err,
                  U238_Pb206_err,
                  Sm147_Nd144_err,
                  Nd143_Nd144_err,
                  Sr87_Sr86_err,
                  Rb87_Sr86_err,
                  Lu176_Hf177_err,
                  Hf176_Hf177_err,
                  Ar36_Ar40_err,
                  Ar39_Ar40_err,
                  Ar39_Ar36_err]

    corr_list = [WetherillErrorCorrelation,
                 TWErrorCorrelation]

    value_error_pairs = {Pb206_U238: Pb206_U238_err,
                         Pb207_U235: Pb207_U235_err,
                         Pb207_Pb206: Pb207_Pb206_err,
                         U238_Pb206: U238_Pb206_err,
                         Nd143_Nd144: Nd143_Nd144_err,
                         Sm147_Nd144: Sm147_Nd144_err,
                         Lu176_Hf177: Lu176_Hf177_err,
                         Hf176_Hf177: Hf176_Hf177_err,
                         Ar39_Ar40: Ar39_Ar40_err,
                         Ar39_Ar36: Ar39_Ar36_err,
                         Ar36_Ar40: Ar36_Ar40_err,
                         Th232_U238: Th232_U238_err,
                         Th230_U238: Th230_U238_err,
                         U234_U238: U234_U238_err}

    UPbColumns = [Pb206_U238, Pb206_U238_err,
                  Pb207_U235, Pb207_U235_err,
                  Pb207_Pb206, Pb207_Pb206_err,
                  WetherillErrorCorrelation,
                  U238_Pb206, U238_Pb206_err,
                  TWErrorCorrelation]

    RbSrColumns = [Sr87_Sr86, Sr87_Sr86_err,
                   Rb87_Sr86, Rb87_Sr86_err,
                   RbConc, RbConc_err,
                   SrConc, SrConc_err]

    SmNdColumns = [Sm147_Nd144, Sm147_Nd144_err,
                   Nd143_Nd144, Nd143_Nd144_err]

    LuHfColumns = [Lu176_Hf177, Lu176_Hf177_err,
                   Hf176_Hf177, Hf176_Hf177_err]

    ArArColumns = [
        Ar39_Ar40, Ar39_Ar40_err, ArAmount,
        Ar36_Ar40, Ar36_Ar40_err,
        Ar39_Ar36, Ar39_Ar36_err
    ]

    for_type = {
        ColumnTypes.Value: value_list,
        ColumnTypes.Error: error_list,
        ColumnTypes.ErrorCorrelation: corr_list,
        ColumnTypes.All: value_list + error_list + corr_list
    }
