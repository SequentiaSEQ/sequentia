// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2021 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <asset.h>
#include <exchangerates.h>
#include <policy/feerate.h>
#include <policy/value.h>
#include <primitives/transaction.h>

#include <tinyformat.h>

#include <cmath>

CFeeRate::CFeeRate(const CAmount& nFeePaid, uint32_t num_bytes)
{
    const int64_t nSize{num_bytes};

    if (nSize > 0) {
        nSatoshisPerK = nFeePaid * 1000 / nSize;
    } else {
        nSatoshisPerK = 0;
    }
}

CAmount CFeeRate::GetFee(uint32_t num_bytes) const
{
    const int64_t nSize{num_bytes};

    // Be explicit that we're converting from a double to int64_t (CAmount) here.
    // We've previously had issues with the silent double->int64_t conversion.
    CAmount nFee{static_cast<CAmount>(std::ceil(nSatoshisPerK * nSize / 1000.0))};

    if (nFee == 0 && nSize != 0) {
        if (nSatoshisPerK > 0) nFee = CAmount(1);
        if (nSatoshisPerK < 0) nFee = CAmount(-1);
    }

    return nFee;
}

CAmount CFeeRate::GetFee(uint32_t num_bytes, const CAsset& asset) const
{
    CValue nFee = CValue(this->GetFee(num_bytes));
    if (g_con_any_asset_fees) {
        nFee = ExchangeRateMap::GetInstance().ConvertValueToAmount(nFee, asset);
    }
    return nFee.GetValue();
}

std::string CFeeRate::ToString(const FeeEstimateMode& fee_estimate_mode) const
{
    switch (fee_estimate_mode) {
    case FeeEstimateMode::SAT_VB: return strprintf("%d.%03d %s/vB", nSatoshisPerK / 1000, nSatoshisPerK % 1000, CURRENCY_ATOM);
    default:                      return strprintf("%d.%08d %s/kvB", nSatoshisPerK / COIN, nSatoshisPerK % COIN, CURRENCY_UNIT);
    }
}
