// P043: deterministic, ROM-free *diagnostic* of two existing EII DAC routes.
// Actual pinned upstream NativeDacChannel and S3528Runtime are exercised.
// Codes encode a bounded DIFFERENTIAL 0.7 V sine, not raw companded sine.
// This is not an EII hardware reference, not an official Studio One test.
#include "native_audio.h"
#include "s3528_runtime.h"
#include <array>
#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>

using namespace eii::analog;
static constexpr double pi=3.1415926535897932384626433832795;
static constexpr unsigned ticksPerDpcmCode=4320; // 120 MHz / 4320 = 27,777.78 Hz
static constexpr double inputCv=3.0;
static constexpr double targetPeak=0.7;
static double ivOf(unsigned c){
    const double m=2490.0*Am6072::magnitudeUnits(std::uint8_t(c))
        *inputCv/(9400.0*2112.0);
    return (c&128u)?-m:m;
}
static std::uint8_t nextDpcm(double target,double& held){
    unsigned best=0;
    double error=std::numeric_limits<double>::infinity(),next=0;
    for(unsigned c=0;c<256;++c) {
        const double v=(50.0/51.0)*(held-ivOf(c));
        const double e=std::abs(v-target);
        if(e<error){error=e;best=c;next=v;}
    }
    held=next;
    return std::uint8_t(best);
}
struct Metric {
    double hz,fast,native,s3528Fast,s3528Native,deltaDb,phaseDeg;
    double filterFastDb,filterNativeDb;
    unsigned codes=0;
};
static Metric measure(double hz,unsigned rate) {
    if(nativeTimeRate%rate)throw std::runtime_error("noninteger rate clock");
    const unsigned tickStep=nativeTimeRate/rate;
    constexpr unsigned seconds=1;
    const unsigned frames=seconds*rate;
    NativeDacCoefficients coefficients;
    NativeDacChannel dac;
    S3528Runtime reconstructionFast(rate),reconstructionNative(rate);
    std::array<std::complex<double>,4> spectrum{};
    std::uint8_t code=0;
    double held=0;
    unsigned events=0;
    for(unsigned n=0;n<frames;++n) {
        unsigned t=n*tickStep;
        const unsigned end=t+tickStep;
        double areaFast=0,areaNative=0;
        while(t<end){
            const unsigned position=t%ticksPerDpcmCode;
            if(position==0) {
                const double secondsAtEvent=double(t)/nativeTimeRate;
                code=nextDpcm(targetPeak*std::sin(2*pi*hz*secondsAtEvent),held);
                ++events;
            }
            unsigned boundary=ticksPerDpcmCode,phase=0;
            for(unsigned e:{192u,384u,576u,768u})
                if(position<e){boundary=e;break;}
            if(position>=192u&&position<384u)phase=1;
            if(position>=576u&&position<768u)phase=2;
            const unsigned dt=std::min(end-t,boundary-position);
            const auto y=dac.advance(dt,{code,255},{inputCv,true},
                                     std::uint8_t(12|phase),coefficients,tl084SwingVolts);
            if(!y.known||!std::isfinite(y.value))
                throw std::runtime_error("native DAC produced unknown/nonfinite frame");
            areaNative+=y.value;
            // Exact production fast/reference nominal deglitch model, including
            // the software-only 1 kHz level match. The hardware circuit does
            // NOT use a static -50 gain: this is the bypass/reference route.
            const double fast=opampSwing(
                -2490.0*Am6072::signedDecodeCurrent(code,inputCv/9400.0)
                 *(-50.0)*fastRouteMatch,tl084SwingVolts);
            areaFast+=fast*dt;
            t+=dt;
        }
        const double fast=areaFast/tickStep,native=areaNative/tickStep;
        const auto a=reconstructionFast.process({fast,true},{35,63});
        const auto b=reconstructionNative.process({native,true},{35,63});
        if(!a.known||!b.known||!std::isfinite(a.value)||!std::isfinite(b.value))
            throw std::runtime_error("S3528 yielded nonfinite/unknown result");
        if(n>=rate/2) {
            const auto phasor=std::polar(2.0/double(rate/2),
                                      -2*pi*hz*(n+0.5)/rate);
            const std::array<double,4> v{fast,native,a.value,b.value};
            for(unsigned k=0;k<4;++k)spectrum[k]+=v[k]*phasor;
        }
    }
    const auto f=std::abs(spectrum[0]),n=std::abs(spectrum[1]);
    if(!(f>1e-9&&n>1e-9)||!std::isfinite(f+n))
        throw std::runtime_error("no valid output spectrum");
    const auto db=[](double a,double b){return 20*std::log10(std::max(a,1e-300)/b);};
    return {hz,f,n,std::abs(spectrum[2]),std::abs(spectrum[3]),
        db(n,f),std::arg(spectrum[1]/spectrum[0])*180/pi,
        db(std::abs(spectrum[2]),f),db(std::abs(spectrum[3]),n),events};
}
int main() try {
    std::cout<<std::setprecision(9);
    std::cout<<"rate_hz,input_hz,fast_amplitude,native_amplitude,native_minus_fast_db,"
                "native_minus_fast_phase_deg,s3528_code35_fast_db,s3528_code35_native_db,dpcm_codes\n";
    unsigned failures=0;
    auto verify=[&](bool ok,const char* name) {
        std::cerr<<(ok?"PASS ":"FAIL ")<<name<<"\n";
        if(!ok)++failures;
    };
    for(unsigned rate:{96000u,192000u}) {
        std::array<Metric,6> rows{};
        unsigned k=0;
        for(double hz:{100.,500.,1000.,3000.,6000.,8000.}) {
            const auto x=measure(hz,rate);
            rows[k++]=x;
            std::cout<<rate<<","<<hz<<","<<x.fast<<","<<x.native<<","
                     <<x.deltaDb<<","<<x.phaseDeg<<","
                     <<x.filterFastDb<<","<<x.filterNativeDb<<","
                     <<x.codes<<"\n";
            if(x.codes<27000||!std::isfinite(x.deltaDb)) {
                ++failures;
                std::cerr<<"FAIL missing codes or nonfinite ratio at "<<hz<<"\n";
            }
        }
        verify(std::abs(rows[2].deltaDb)<2.5,
               "1 kHz: reference and switched DAC approximately level matched");
        verify(rows[0].deltaDb>rows[2].deltaDb+8,
               "100 Hz: actual switched DAC has different low-frequency response");
        verify(rows[4].deltaDb<rows[2].deltaDb-6,
               "6 kHz: actual switched DAC has different high-frequency response");
        verify(rows[0].filterFastDb>-.7&&rows[0].filterNativeDb>-.7,
               "S3528 code35 preserves 100 Hz in both routes");
        verify(rows[4].filterFastDb< -20&&rows[4].filterNativeDb< -20,
               "S3528 code35 attenuates 6 kHz in both routes");
        // Negative mutant native=fast would fail both the low and high
        // cross-route delta gates, independent of amplitude normalization.
    }
    std::cerr<<(failures?"P043 DIAGNOSTIC FAIL":"P043 DPCM BOTH DAC ROUTES DIAGNOSTIC PASS")
             <<" failures="<<failures
             <<" ; NO ORIGINAL HARDWARE REFERENCE, NO FIDELITY CLAIM\n";
    return failures?1:0;
} catch(const std::exception& e) {
    std::cerr<<"P043 DIAGNOSTIC FAIL: "<<e.what()<<"\n";
    return 2;
}
