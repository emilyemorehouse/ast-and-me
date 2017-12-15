"""Library that exposes various tables found in the StringPrep RFC 3454.

There are two kinds of tables: sets, for which a member test is provided,
and mappings, for which a mapping function is provided.
"""
from unicodedata import ucd_3_2_0 as unicodedata
assert unicodedata.unidata_version == '3.2.0'


def in_table_a1(code):
    if unicodedata.category(code) != 'Cn':
        return False
    c = ord(code)
    if 64976 <= c < 65008:
        return False
    return c & 65535 not in (65534, 65535)


b1_set = set([173, 847, 6150, 6155, 6156, 6157, 8203, 8204, 8205, 8288, 
    65279] + list(range(65024, 65040)))


def in_table_b1(code):
    return ord(code) in b1_set


b3_exceptions = {(181): 'μ', (223): 'ss', (304): 'i̇', (329): 'ʼn', (383):
    's', (496): 'ǰ', (837): 'ι', (890): ' ι', (912): 'ΐ', (944): 'ΰ',
    (962): 'σ', (976): 'β', (977): 'θ', (978): 'υ', (979): 'ύ', (980): 'ϋ',
    (981): 'φ', (982): 'π', (1008): 'κ', (1009): 'ρ', (1010): 'σ', (1013):
    'ε', (1415): 'եւ', (7830): 'ẖ', (7831): 'ẗ', (7832): 'ẘ', (7833):
    'ẙ', (7834): 'aʾ', (7835): 'ṡ', (8016): 'ὐ', (8018): 'ὒ', (8020):
    'ὔ', (8022): 'ὖ', (8064): 'ἀι', (8065): 'ἁι', (8066): 'ἂι', (8067):
    'ἃι', (8068): 'ἄι', (8069): 'ἅι', (8070): 'ἆι', (8071): 'ἇι', (8072):
    'ἀι', (8073): 'ἁι', (8074): 'ἂι', (8075): 'ἃι', (8076): 'ἄι', (8077):
    'ἅι', (8078): 'ἆι', (8079): 'ἇι', (8080): 'ἠι', (8081): 'ἡι', (8082):
    'ἢι', (8083): 'ἣι', (8084): 'ἤι', (8085): 'ἥι', (8086): 'ἦι', (8087):
    'ἧι', (8088): 'ἠι', (8089): 'ἡι', (8090): 'ἢι', (8091): 'ἣι', (8092):
    'ἤι', (8093): 'ἥι', (8094): 'ἦι', (8095): 'ἧι', (8096): 'ὠι', (8097):
    'ὡι', (8098): 'ὢι', (8099): 'ὣι', (8100): 'ὤι', (8101): 'ὥι', (8102):
    'ὦι', (8103): 'ὧι', (8104): 'ὠι', (8105): 'ὡι', (8106): 'ὢι', (8107):
    'ὣι', (8108): 'ὤι', (8109): 'ὥι', (8110): 'ὦι', (8111): 'ὧι', (8114):
    'ὰι', (8115): 'αι', (8116): 'άι', (8118): 'ᾶ', (8119): 'ᾶι', (8124):
    'αι', (8126): 'ι', (8130): 'ὴι', (8131): 'ηι', (8132): 'ήι', (8134):
    'ῆ', (8135): 'ῆι', (8140): 'ηι', (8146): 'ῒ', (8147): 'ΐ', (8150):
    'ῖ', (8151): 'ῗ', (8162): 'ῢ', (8163): 'ΰ', (8164): 'ῤ', (8166):
    'ῦ', (8167): 'ῧ', (8178): 'ὼι', (8179): 'ωι', (8180): 'ώι', (8182):
    'ῶ', (8183): 'ῶι', (8188): 'ωι', (8360): 'rs', (8450): 'c', (8451):
    '°c', (8455): 'ɛ', (8457): '°f', (8459): 'h', (8460): 'h', (8461): 'h',
    (8464): 'i', (8465): 'i', (8466): 'l', (8469): 'n', (8470): 'no', (8473
    ): 'p', (8474): 'q', (8475): 'r', (8476): 'r', (8477): 'r', (8480):
    'sm', (8481): 'tel', (8482): 'tm', (8484): 'z', (8488): 'z', (8492):
    'b', (8493): 'c', (8496): 'e', (8497): 'f', (8499): 'm', (8510): 'γ', (
    8511): 'π', (8517): 'd', (13169): 'hpa', (13171): 'au', (13173): 'ov',
    (13184): 'pa', (13185): 'na', (13186): 'μa', (13187): 'ma', (13188):
    'ka', (13189): 'kb', (13190): 'mb', (13191): 'gb', (13194): 'pf', (
    13195): 'nf', (13196): 'μf', (13200): 'hz', (13201): 'khz', (13202):
    'mhz', (13203): 'ghz', (13204): 'thz', (13225): 'pa', (13226): 'kpa', (
    13227): 'mpa', (13228): 'gpa', (13236): 'pv', (13237): 'nv', (13238):
    'μv', (13239): 'mv', (13240): 'kv', (13241): 'mv', (13242): 'pw', (
    13243): 'nw', (13244): 'μw', (13245): 'mw', (13246): 'kw', (13247):
    'mw', (13248): 'kω', (13249): 'mω', (13251): 'bq', (13254): 'c∕kg', (
    13255): 'co.', (13256): 'db', (13257): 'gy', (13259): 'hp', (13261):
    'kk', (13262): 'km', (13271): 'ph', (13273): 'ppm', (13274): 'pr', (
    13276): 'sv', (13277): 'wb', (64256): 'ff', (64257): 'fi', (64258):
    'fl', (64259): 'ffi', (64260): 'ffl', (64261): 'st', (64262): 'st', (
    64275): 'մն', (64276): 'մե', (64277): 'մի', (64278): 'վն', (64279):
    'մխ', (119808): 'a', (119809): 'b', (119810): 'c', (119811): 'd', (
    119812): 'e', (119813): 'f', (119814): 'g', (119815): 'h', (119816):
    'i', (119817): 'j', (119818): 'k', (119819): 'l', (119820): 'm', (
    119821): 'n', (119822): 'o', (119823): 'p', (119824): 'q', (119825):
    'r', (119826): 's', (119827): 't', (119828): 'u', (119829): 'v', (
    119830): 'w', (119831): 'x', (119832): 'y', (119833): 'z', (119860):
    'a', (119861): 'b', (119862): 'c', (119863): 'd', (119864): 'e', (
    119865): 'f', (119866): 'g', (119867): 'h', (119868): 'i', (119869):
    'j', (119870): 'k', (119871): 'l', (119872): 'm', (119873): 'n', (
    119874): 'o', (119875): 'p', (119876): 'q', (119877): 'r', (119878):
    's', (119879): 't', (119880): 'u', (119881): 'v', (119882): 'w', (
    119883): 'x', (119884): 'y', (119885): 'z', (119912): 'a', (119913):
    'b', (119914): 'c', (119915): 'd', (119916): 'e', (119917): 'f', (
    119918): 'g', (119919): 'h', (119920): 'i', (119921): 'j', (119922):
    'k', (119923): 'l', (119924): 'm', (119925): 'n', (119926): 'o', (
    119927): 'p', (119928): 'q', (119929): 'r', (119930): 's', (119931):
    't', (119932): 'u', (119933): 'v', (119934): 'w', (119935): 'x', (
    119936): 'y', (119937): 'z', (119964): 'a', (119966): 'c', (119967):
    'd', (119970): 'g', (119973): 'j', (119974): 'k', (119977): 'n', (
    119978): 'o', (119979): 'p', (119980): 'q', (119982): 's', (119983):
    't', (119984): 'u', (119985): 'v', (119986): 'w', (119987): 'x', (
    119988): 'y', (119989): 'z', (120016): 'a', (120017): 'b', (120018):
    'c', (120019): 'd', (120020): 'e', (120021): 'f', (120022): 'g', (
    120023): 'h', (120024): 'i', (120025): 'j', (120026): 'k', (120027):
    'l', (120028): 'm', (120029): 'n', (120030): 'o', (120031): 'p', (
    120032): 'q', (120033): 'r', (120034): 's', (120035): 't', (120036):
    'u', (120037): 'v', (120038): 'w', (120039): 'x', (120040): 'y', (
    120041): 'z', (120068): 'a', (120069): 'b', (120071): 'd', (120072):
    'e', (120073): 'f', (120074): 'g', (120077): 'j', (120078): 'k', (
    120079): 'l', (120080): 'm', (120081): 'n', (120082): 'o', (120083):
    'p', (120084): 'q', (120086): 's', (120087): 't', (120088): 'u', (
    120089): 'v', (120090): 'w', (120091): 'x', (120092): 'y', (120120):
    'a', (120121): 'b', (120123): 'd', (120124): 'e', (120125): 'f', (
    120126): 'g', (120128): 'i', (120129): 'j', (120130): 'k', (120131):
    'l', (120132): 'm', (120134): 'o', (120138): 's', (120139): 't', (
    120140): 'u', (120141): 'v', (120142): 'w', (120143): 'x', (120144):
    'y', (120172): 'a', (120173): 'b', (120174): 'c', (120175): 'd', (
    120176): 'e', (120177): 'f', (120178): 'g', (120179): 'h', (120180):
    'i', (120181): 'j', (120182): 'k', (120183): 'l', (120184): 'm', (
    120185): 'n', (120186): 'o', (120187): 'p', (120188): 'q', (120189):
    'r', (120190): 's', (120191): 't', (120192): 'u', (120193): 'v', (
    120194): 'w', (120195): 'x', (120196): 'y', (120197): 'z', (120224):
    'a', (120225): 'b', (120226): 'c', (120227): 'd', (120228): 'e', (
    120229): 'f', (120230): 'g', (120231): 'h', (120232): 'i', (120233):
    'j', (120234): 'k', (120235): 'l', (120236): 'm', (120237): 'n', (
    120238): 'o', (120239): 'p', (120240): 'q', (120241): 'r', (120242):
    's', (120243): 't', (120244): 'u', (120245): 'v', (120246): 'w', (
    120247): 'x', (120248): 'y', (120249): 'z', (120276): 'a', (120277):
    'b', (120278): 'c', (120279): 'd', (120280): 'e', (120281): 'f', (
    120282): 'g', (120283): 'h', (120284): 'i', (120285): 'j', (120286):
    'k', (120287): 'l', (120288): 'm', (120289): 'n', (120290): 'o', (
    120291): 'p', (120292): 'q', (120293): 'r', (120294): 's', (120295):
    't', (120296): 'u', (120297): 'v', (120298): 'w', (120299): 'x', (
    120300): 'y', (120301): 'z', (120328): 'a', (120329): 'b', (120330):
    'c', (120331): 'd', (120332): 'e', (120333): 'f', (120334): 'g', (
    120335): 'h', (120336): 'i', (120337): 'j', (120338): 'k', (120339):
    'l', (120340): 'm', (120341): 'n', (120342): 'o', (120343): 'p', (
    120344): 'q', (120345): 'r', (120346): 's', (120347): 't', (120348):
    'u', (120349): 'v', (120350): 'w', (120351): 'x', (120352): 'y', (
    120353): 'z', (120380): 'a', (120381): 'b', (120382): 'c', (120383):
    'd', (120384): 'e', (120385): 'f', (120386): 'g', (120387): 'h', (
    120388): 'i', (120389): 'j', (120390): 'k', (120391): 'l', (120392):
    'm', (120393): 'n', (120394): 'o', (120395): 'p', (120396): 'q', (
    120397): 'r', (120398): 's', (120399): 't', (120400): 'u', (120401):
    'v', (120402): 'w', (120403): 'x', (120404): 'y', (120405): 'z', (
    120432): 'a', (120433): 'b', (120434): 'c', (120435): 'd', (120436):
    'e', (120437): 'f', (120438): 'g', (120439): 'h', (120440): 'i', (
    120441): 'j', (120442): 'k', (120443): 'l', (120444): 'm', (120445):
    'n', (120446): 'o', (120447): 'p', (120448): 'q', (120449): 'r', (
    120450): 's', (120451): 't', (120452): 'u', (120453): 'v', (120454):
    'w', (120455): 'x', (120456): 'y', (120457): 'z', (120488): 'α', (
    120489): 'β', (120490): 'γ', (120491): 'δ', (120492): 'ε', (120493):
    'ζ', (120494): 'η', (120495): 'θ', (120496): 'ι', (120497): 'κ', (
    120498): 'λ', (120499): 'μ', (120500): 'ν', (120501): 'ξ', (120502):
    'ο', (120503): 'π', (120504): 'ρ', (120505): 'θ', (120506): 'σ', (
    120507): 'τ', (120508): 'υ', (120509): 'φ', (120510): 'χ', (120511):
    'ψ', (120512): 'ω', (120531): 'σ', (120546): 'α', (120547): 'β', (
    120548): 'γ', (120549): 'δ', (120550): 'ε', (120551): 'ζ', (120552):
    'η', (120553): 'θ', (120554): 'ι', (120555): 'κ', (120556): 'λ', (
    120557): 'μ', (120558): 'ν', (120559): 'ξ', (120560): 'ο', (120561):
    'π', (120562): 'ρ', (120563): 'θ', (120564): 'σ', (120565): 'τ', (
    120566): 'υ', (120567): 'φ', (120568): 'χ', (120569): 'ψ', (120570):
    'ω', (120589): 'σ', (120604): 'α', (120605): 'β', (120606): 'γ', (
    120607): 'δ', (120608): 'ε', (120609): 'ζ', (120610): 'η', (120611):
    'θ', (120612): 'ι', (120613): 'κ', (120614): 'λ', (120615): 'μ', (
    120616): 'ν', (120617): 'ξ', (120618): 'ο', (120619): 'π', (120620):
    'ρ', (120621): 'θ', (120622): 'σ', (120623): 'τ', (120624): 'υ', (
    120625): 'φ', (120626): 'χ', (120627): 'ψ', (120628): 'ω', (120647):
    'σ', (120662): 'α', (120663): 'β', (120664): 'γ', (120665): 'δ', (
    120666): 'ε', (120667): 'ζ', (120668): 'η', (120669): 'θ', (120670):
    'ι', (120671): 'κ', (120672): 'λ', (120673): 'μ', (120674): 'ν', (
    120675): 'ξ', (120676): 'ο', (120677): 'π', (120678): 'ρ', (120679):
    'θ', (120680): 'σ', (120681): 'τ', (120682): 'υ', (120683): 'φ', (
    120684): 'χ', (120685): 'ψ', (120686): 'ω', (120705): 'σ', (120720):
    'α', (120721): 'β', (120722): 'γ', (120723): 'δ', (120724): 'ε', (
    120725): 'ζ', (120726): 'η', (120727): 'θ', (120728): 'ι', (120729):
    'κ', (120730): 'λ', (120731): 'μ', (120732): 'ν', (120733): 'ξ', (
    120734): 'ο', (120735): 'π', (120736): 'ρ', (120737): 'θ', (120738):
    'σ', (120739): 'τ', (120740): 'υ', (120741): 'φ', (120742): 'χ', (
    120743): 'ψ', (120744): 'ω', (120763): 'σ'}


def map_table_b3(code):
    r = b3_exceptions.get(ord(code))
    if r is not None:
        return r
    return code.lower()


def map_table_b2(a):
    al = map_table_b3(a)
    b = unicodedata.normalize('NFKC', al)
    bl = ''.join([map_table_b3(ch) for ch in b])
    c = unicodedata.normalize('NFKC', bl)
    if b != c:
        return c
    else:
        return al


def in_table_c11(code):
    return code == ' '


def in_table_c12(code):
    return unicodedata.category(code) == 'Zs' and code != ' '


def in_table_c11_c12(code):
    return unicodedata.category(code) == 'Zs'


def in_table_c21(code):
    return ord(code) < 128 and unicodedata.category(code) == 'Cc'


c22_specials = set([1757, 1807, 6158, 8204, 8205, 8232, 8233, 65279] + list
    (range(8288, 8292)) + list(range(8298, 8304)) + list(range(65529, 65533
    )) + list(range(119155, 119163)))


def in_table_c22(code):
    c = ord(code)
    if c < 128:
        return False
    if unicodedata.category(code) == 'Cc':
        return True
    return c in c22_specials


def in_table_c21_c22(code):
    return unicodedata.category(code) == 'Cc' or ord(code) in c22_specials


def in_table_c3(code):
    return unicodedata.category(code) == 'Co'


def in_table_c4(code):
    c = ord(code)
    if c < 64976:
        return False
    if c < 65008:
        return True
    return ord(code) & 65535 in (65534, 65535)


def in_table_c5(code):
    return unicodedata.category(code) == 'Cs'


c6_set = set(range(65529, 65534))


def in_table_c6(code):
    return ord(code) in c6_set


c7_set = set(range(12272, 12284))


def in_table_c7(code):
    return ord(code) in c7_set


c8_set = set([832, 833, 8206, 8207] + list(range(8234, 8239)) + list(range(
    8298, 8304)))


def in_table_c8(code):
    return ord(code) in c8_set


c9_set = set([917505] + list(range(917536, 917632)))


def in_table_c9(code):
    return ord(code) in c9_set


def in_table_d1(code):
    return unicodedata.bidirectional(code) in ('R', 'AL')


def in_table_d2(code):
    return unicodedata.bidirectional(code) == 'L'
