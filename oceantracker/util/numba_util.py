import numpy as np
from os import environ
import os


import numba as nb
from numba import prange
# give direct access to some numba stuff.
from time import perf_counter

numba_func_info={}
def njitOT(func):
    # add ability to inspect the functions after compilation at end for SIMD code
    #num_func = njit(func, *args)

    cache= 'OCEANTRACKER_NUMBA_CACHING' in os.environ and os.environ['OCEANTRACKER_NUMBA_CACHING'] == '1'
    num_func = nb.njit(func,
                       cache=cache,
                       fastmath =  'NUMBA_FASTMATH' not in os.environ or os.environ['NUMBA_FASTMATH'] =='1',
                       )

    if hasattr(func,'__name__'):
        # record numba version of the function
        key = func.__module__ + '.' + func.__name__
        numba_func_info[key] = num_func

    return num_func



def njitOTparallel(func):
    # add ability to inspect the functions after compilation at end for SIMD code
    #num_func = njit(func, *args)

    num_func = nb.njit(func,
                       cache='OCEANTRACKER_NUMBA_CACHING' in os.environ and os.environ['OCEANTRACKER_NUMBA_CACHING'] == '1',
                       parallel= 'OCEANTRACKER_USE_PARALLEL_THREADS' not in os.environ or os.environ['OCEANTRACKER_USE_PARALLEL_THREADS'] =='1',
                       fastmath =  'NUMBA_FASTMATH' not in os.environ or os.environ['NUMBA_FASTMATH'] =='1',
                       nogil=True,
                       #fastmath='NUMBA_FASTMATH' not in os.environ or os.environ['NUMBA_FASTMATH'] =='1'
                       )

    if hasattr(func,'__name__'):
        # record numba version of the function
        key = func.__module__ + '.' + func.__name__
        numba_func_info[key] = num_func

    return num_func

@nb.njit
def find_last_less_than(x, x_val):
    # find first value just less that x_val in 1D array x
    n = 0
    for n in range(x.size-1):
        if x[n] >= x_val:
           break
    return n


def get_numba_func_info():
    d = dict( config={key: val for key, val in nb.config.__dict__.items()
                   if not key.startswith('_') and type(val) in [None, int, str, float] },
             modules={}     )
    from numba.misc.numba_sysinfo import get_sysinfo
    d['sysinfo']= get_sysinfo()

    for name, func in numba_func_info.items():

        if hasattr(func, 'signatures'):  # only code that has been compiled has a sig
            mod, fname = name.rsplit('.',1)
            fd = []
            for nsig, sig  in enumerate(list(func.signatures)):
                p = dict(signature=str(sig))
                p['simd_instructions'],code= count_simd_intructions(func, sig=nsig)
                #p['code'] = code
                fd.append(p)

            if mod not in d['modules']: d['modules'][mod] = {}
            d['modules'][mod][name] = fd
    d['modules'] = {key : d['modules'][key] for key in  sorted(d['modules'].keys())}
    return d

avx_instructions ='vmovapd|vmulpd|vaddpd|vsubpd|vfmadd213pd|vfmadd231pd|vfmadd132pd|vmulsd|vaddsd|vmosd|vsubsd|vbroadcastss|vbroadcastsd|vblendpd|vshufpd|vroundpd|vroundsd|vxorpd|vfnmadd231pd|vfnmadd213pd|vfnmadd132pd|vandpd|vmaxpd|vmovmskpd|vcmppd|vpaddd|vbroadcastf128|vinsertf128|vextractf128|vfmsub231pd|vfmsub132pd|vfmsub213pd|vmaskmovps|vmaskmovpd|vpermilps|vpermilpd|vperm2f128|vzeroall|vzeroupper|vpbroadcastb|vpbroadcastw|vpbroadcastd|vpbroadcastq|vbroadcasti128|vinserti128|vextracti128|vpminud|vpmuludq|vgatherdpd|vgatherqpd|vgatherdps|vgatherqps|vpgatherdd|vpgatherdq|vpgatherqd|vpgatherqq|vpmaskmovd|vpmaskmovq|vpermps|vpermd|vpermpd|vpermq|vperm2i128|vpblendd|vpsllvd|vpsllvq|vpsrlvd|vpsrlvq|vpsravd|vblendmpd|vblendmps|vpblendmd|vpblendmq|vpblendmb|vpblendmw|vpcmpd|vpcmpud|vpcmpq|vpcmpuq|vpcmpb|vpcmpub|vpcmpw|vpcmpuw|vptestmd|vptestmq|vptestnmd|vptestnmq|vptestmb|vptestmw|vptestnmb|vptestnmw|vcompresspd|vcompressps|vpcompressd|vpcompressq|vexpandpd|vexpandps|vpexpandd|vpexpandq|vpermb|vpermw|vpermt2b|vpermt2w|vpermi2pd|vpermi2ps|vpermi2d|vpermi2q|vpermi2b|vpermi2w|vpermt2ps|vpermt2pd|vpermt2d|vpermt2q|vshufDataByTriTemp2x4|vshuff64x2|vshuffi32x4|vshuffi64x2|vpmultishiftqb|vpternlogd|vpternlogq|vpmovqd|vpmovsqd|vpmovusqd|vpmovqw|vpmovsqw|vpmovusqw|vpmovqb|vpmovsqb|vpmovusqb|vpmovdw|vpmovsdw|vpmovusdw|vpmovdb|vpmovsdb|vpmovusdb|vpmovwb|vpmovswb|vpmovuswb|vcvtps2udq|vcvtpd2udq|vcvttps2udq|vcvttpd2udq|vcvtss2usi|vcvtsd2usi|vcvttss2usi|vcvttsd2usi|vcvtps2qq|vcvtpd2qq|vcvtps2uqq|vcvtpd2uqq|vcvttps2qq|vcvttpd2qq|vcvttps2uqq|vcvttpd2uqq|vcvtudq2ps|vcvtudq2pd|vcvtusi2ps|vcvtusi2pd|vcvtusi2sd|vcvtusi2ss|vcvtuqq2ps|vcvtuqq2pd|vcvtqq2pd|vcvtqq2ps|vgetexppd|vgetexpps|vgetexpsd|vgetexpss|vgetmantpd|vgetmantps|vgetmantsd|vgetmantss|vfixupimmpd|vfixupimmps|vfixupimmsd|vfixupimmss|vrcp14pd|vrcp14ps|vrcp14sd|vrcp14ss|vrndscaleps|vrndscalepd|vrndscaless|vrndscalesd|vrsqrt14pd|vrsqrt14ps|vrsqrt14sd|vrsqrt14ss|vscalefps|vscalefpd|vscalefss|vscalefsd|valignd|valignq|vdbpsadbw|vpabsq|vpmaxsq|vpmaxuq|vpminsq|vpminuq|vprold|vprolvd|vprolq|vprolvq|vprord|vprorvd|vprorq|vprorvq|vpscatterdd|vpscatterdq|vpscatterqd|vpscatterqq|vscatterdps|vscatterdpd|vscatterqps|vscatterqpd|vpconflictd|vpconflictq|vplzcntd|vplzcntq|vpbroadcastmb2q|vpbroadcastmw2d|vexp2pd|vexp2ps|vrcp28pd|vrcp28ps|vrcp28sd|vrcp28ss|vrsqrt28pd|vrsqrt28ps|vrsqrt28sd|vrsqrt28ss|vgatherpf0dps|vgatherpf0qps|vgatherpf0dpd|vgatherpf0qpd|vgatherpf1dps|vgatherpf1qps|vgatherpf1dpd|vgatherpf1qpd|vscatterpf0dps|vscatterpf0qps|vscatterpf0dpd|vscatterpf0qpd|vscatterpf1dps|vscatterpf1qps|vscatterpf1dpd|vscatterpf1qpd|vfpclassps|vfpclasspd|vfpclassss|vfpclasssd|vrangeps|vrangepd|vrangess|vrangesd|vreduceps|vreducepd|vreducess|vreducesd|vpmovm2d|vpmovm2q|vpmovm2b|vpmovm2w|vpmovd2m|vpmovq2m|vpmovb2m|vpmovw2m|vpmullq|vpmadd52luq|vpmadd52huq|v4fmaddps|v4fmaddss|v4fnmaddps|v4fnmaddss|vp4dpwssd|vp4dpwssds|vpdpbusd|vpdpbusds|vpdpwssd|vpdpwssds|vpcompressb|vpcompressw|vpexpandb|vpexpandw|vpshld|vpshldv|vpshrd|vpshrdv|vpopcntd|vpopcntq|vpopcntb|vpopcntw|vpshufbitqmb|gDataByTrip8affineinvqb|gDataByTrip8affineqb|gDataByTrip8mulb|vpclmulqdq|vaesdec|vaesdeclast|vaesenc|vaesenclast'.split('|')
avx_instructions += 'addps|addss|andnps|andps|cmpps|cmpss|comiss|cvtpi2ps|cvtps2pi|cvtsi2ss|cvtss2s|cvttps2pi|cvttss2si|divps|divss|ldmxcsr|maxps|maxss|minps|minss|movaps|movhlps|movhps|movlhps|movlps|movmskps|movntps|movss|movups|mulps|mulss|orps|rcpps|rcpss|rsqrtps|rsqrtss|shufps|sqrtps|sqrtss|stmxcsr|subps|subss|ucomiss|unpckhps|unpcklps|xorps|pavgb|pavgw|pextrw|pinsrw|pmaxsw|pmaxub|pminsw|pminub|pmovmskb|psadbw|pshufw'.split('|')
avx_instructions =['%ymm','%xmm'] + list(set(avx_instructions))
def count_simd_intructions(func, sig=0,keep_zeros=False):

    simd_instruct={}


    # hack a full list of avx
    if not hasattr(func,'inspect_asm'):
        print(func.__name__, 'Nested fuction no separate code')
        return simd_instruct

    code = func.inspect_asm(func.signatures[sig])


    for  i in avx_instructions:
        simd_instruct[i] = code.count(i)

    # put in alphabetical order
    simd_instruct  = {i: simd_instruct[i] for i  in sorted(simd_instruct.keys()) }

    # remove unused counts
    if not keep_zeros:
        simd_instruct = {i: count for i, count in simd_instruct.items() if count > 0}

    code = code.replace('\t','    ').split('\n')
    return simd_instruct, code

def compare_simd(numba_fun_list,show=True):
    counts=[]
    for  f in numba_fun_list:
        counts.append(count_simd_intructions(f,keep_zeros=True))

    # collect results
    comp ={}
    for key  in counts[0].keys():
        comp[key]= np.zeros((len(numba_fun_list),),dtype=np.int32)
        for n, c in enumerate(counts):
            if key in  c.keys():
                comp[key][n] += c[key]

    # discard those with all zeros
    comp={key:item.tolist() for key,item in comp.items() if item.sum() > 0 }
    comp = {key:comp[key] for key in sorted(comp.keys()) } # alpbetacl order
    out = dict(names=[f.__name__ for f in numba_fun_list])
    out.update(comp)
    if show:
        for key, item in out.items():
            print(f'{key} \t\t {item}')
    return out


def time_numba_code(fun,*args, number=10):

    # compile if neded
    fun(*args)

    t0 = perf_counter()
    for n in range(number):
        fun(*args)
    return (perf_counter()-t0)/number




