#ifndef CASTRO_HABEC_F_H
#define CASTRO_HABEC_F_H

#include <AMReX_ArrayLim.H>
#include <AMReX_BLFort.H>

#ifdef __cplusplus
extern "C" {
#else
#define RadBoundCond int
#endif

  void hbflx(BL_FORT_FAB_ARG(flux),
             BL_FORT_FAB_ARG(soln),
             ARLIM_P(reglo), ARLIM_P(reghi), 
             const int& cdir, const RadBoundCond& bct,
             const int& bho, const amrex::Real& bcl,
             const amrex::Real* bcval, ARLIM_P(fslo), ARLIM_P(fshi), 
             const BL_FORT_IFAB_ARG(mask),
             BL_FORT_FAB_ARG(bcoefs),
             const amrex::Real& beta, const amrex::Real* dx, const int& inhom);

  void hbflx3(BL_FORT_FAB_ARG(flux),
              BL_FORT_FAB_ARG(soln),
              ARLIM_P(reglo), ARLIM_P(reghi),
              const int& cdir, const int& bctype, const int* tf,
              const int& bho, const amrex::Real& bcl,
              const BL_FORT_FAB_ARG(bcval),
              const BL_FORT_IFAB_ARG(mask),
              BL_FORT_FAB_ARG(bcoefs),
              const amrex::Real& beta, const amrex::Real* dx,
              const amrex::Real& flux_factor, const amrex::Real* r,
              const int& inhom,
              const amrex::Real* spa, ARLIM_P(splo), ARLIM_P(sphi));

  void hdterm(BL_FORT_FAB_ARG(dterm),
              BL_FORT_FAB_ARG(soln),
              ARLIM_P(reglo), ARLIM_P(reghi),
              const int& cdir, const RadBoundCond& bct,
              const amrex::Real& bcl,
              const BL_FORT_FAB_ARG(bcval),
              const BL_FORT_IFAB_ARG(mask),
              BL_FORT_FAB_ARG(dcoefs),
              const amrex::Real* dx);

  void hdterm3(BL_FORT_FAB_ARG(dterm),
               BL_FORT_FAB_ARG(soln),
               ARLIM_P(reglo), ARLIM_P(reghi),
               const int& cdir, const int& bctype, const int* tf,
               const amrex::Real& bcl,
               const BL_FORT_FAB_ARG(bcval),
               const BL_FORT_IFAB_ARG(mask),
               BL_FORT_FAB_ARG(dcoefs),
               const amrex::Real* dx);

#ifdef __cplusplus
};
#endif

#endif
