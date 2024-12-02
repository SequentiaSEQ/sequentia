#!/usr/bin/env python3
# Copyright (c) 2017-2020 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Tests fees being paid in any asset feature"""

from test_framework.blocktools import COINBASE_MATURITY
from test_framework.test_framework import BitcoinTestFramework
from decimal import Decimal
from test_framework.util import (
    assert_raises_rpc_error, assert_equal
)

class AnyAssetFeeScenariosTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 2
        self.extra_args = [[
            "-blindedaddresses=0",
            "-walletrbf=1",
            "-initialfreecoins=1000000000",
            "-con_blocksubsidy=0",
            "-con_connect_genesis_outputs=1",
            "-con_any_asset_fees=1",
            "-defaultpeggedassetname=test",
            "-txindex=1",
        ]] * self.num_nodes
        self.extra_args[0].append("-anyonecanspendaremine=1")

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def init(self):
        self.generate(self.nodes[0], COINBASE_MATURITY + 1)
        self.sync_all()

        assert self.nodes[0].dumpassetlabels() == {'test': 'b2e15d0d7a0c94e4e2ce0fe6e8691b9e451377f6e46e8045a86f7c4b5d4f0f23'}
        assert self.nodes[0].getfeeexchangerates() == { 'test': 100000000 }
        self.test = self.nodes[0].dumpassetlabels()['test']

        self.node0_mining_address = self.nodes[0].getnewaddress()
        self.node0_address = self.nodes[0].getnewaddress()
        self.node1_address = self.nodes[1].getnewaddress()

        # AAPL
        self.issue_amount1 = Decimal('100')
        self.issuance1 = self.nodes[0].issueasset(self.issue_amount1, 1, False)
        self.asset1 = self.issuance1['asset']
        self.issuance_txid1 = self.issuance1['txid']
        self.issuance_vin1 = self.issuance1['vin']

        self.nodes[0].generatetoaddress(1, self.node0_mining_address, invalid_call=False)

        # TSLA
        self.issue_amount2 = Decimal('200')
        self.issuance2 = self.nodes[0].issueasset(self.issue_amount2, 1, False)
        self.asset2 = self.issuance2['asset']
        self.issuance_txid2 = self.issuance2['txid']
        self.issuance_vin2 = self.issuance2['vin']

        self.nodes[0].generatetoaddress(1, self.node0_mining_address, invalid_call=False)

        # MSTR
        self.issue_amount3 = Decimal('300')
        self.issuance3 = self.nodes[0].issueasset(self.issue_amount3, 1, False)
        self.asset3 = self.issuance3['asset']
        self.issuance_txid3 = self.issuance3['txid']
        self.issuance_vin3 = self.issuance3['vin']

        self.nodes[0].generatetoaddress(1, self.node0_mining_address, invalid_call=False)

        # USDT
        self.issue_amount4 = Decimal('10000000')
        self.issuance4 = self.nodes[0].issueasset(assetamount = self.issue_amount4, tokenamount= 1, blind = False, denomination = 2)
        self.asset4 = self.issuance4['asset']
        self.issuance_txid4 = self.issuance4['txid']
        self.issuance_vin4 = self.issuance4['vin']

        self.nodes[0].generatetoaddress(1, self.node0_mining_address, invalid_call=False)

        # UNKW
        self.issue_amount5 = Decimal('1000')
        self.issuance5 = self.nodes[0].issueasset(self.issue_amount5, 1, False)
        self.asset5 = self.issuance5['asset']
        self.issuance_txid5 = self.issuance5['txid']
        self.issuance_vin5 = self.issuance5['vin']

        self.nodes[0].generatetoaddress(1, self.node0_mining_address, invalid_call=False)

        new_rates = { "test": 100000000, self.asset1: 23493000000, self.asset2: 33289000000, self.asset3: 38884000000, self.asset4: 99990000, self.asset5: 100000000}
        self.nodes[0].setfeeexchangerates(new_rates)
        assert self.nodes[0].getfeeexchangerates() == new_rates
        new_rates = { "test": 100000000, self.asset1: 23493000000, self.asset2: 33289000000, self.asset3: 38884000000, self.asset4: 99990000}
        self.nodes[1].setfeeexchangerates(new_rates)
        assert self.nodes[1].getfeeexchangerates() == new_rates

        self.nodes[0].sendtoaddress(address=self.node0_address, amount=self.nodes[0].getbalance()['test'], assetlabel=self.test, subtractfeefromamount=True)
        self.nodes[0].generatetoaddress(1, self.node0_mining_address, invalid_call=False)

        #unspent = self.nodes[0].listunspent()
        #print(json.dumps(unspent, indent=4, sort_keys=True, default=str))

        self.nodes[0].sendtoaddress(address=self.node0_address, amount=100.0, assetlabel=self.asset1, fee_asset_label=self.test)
        self.nodes[0].sendtoaddress(address=self.node0_address, amount=200.0, assetlabel=self.asset2, fee_asset_label=self.test)
        self.nodes[0].sendtoaddress(address=self.node0_address, amount=300.0, assetlabel=self.asset3, fee_asset_label=self.test)
        self.nodes[0].sendtoaddress(address=self.node0_address, amount=10000000.0, assetlabel=self.asset4, fee_asset_label=self.test)
        self.nodes[0].sendtoaddress(address=self.node0_address, amount=1000.0, assetlabel=self.asset5, fee_asset_label=self.test)

        self.nodes[0].sendtoaddress(address=self.node0_address, amount=self.nodes[0].getbalance()['test'], assetlabel=self.test, subtractfeefromamount=True)
        self.nodes[0].generatetoaddress(1, self.node0_mining_address, invalid_call=False)



        self.issuance_addr1 = self.nodes[0].gettransaction(self.issuance_txid1)['details'][0]['address']
        self.nodes[1].importaddress(self.issuance_addr1)
        self.issuance_addr2 = self.nodes[0].gettransaction(self.issuance_txid2)['details'][0]['address']
        self.nodes[1].importaddress(self.issuance_addr2)
        self.issuance_addr3 = self.nodes[0].gettransaction(self.issuance_txid3)['details'][0]['address']
        self.nodes[1].importaddress(self.issuance_addr3)
        self.issuance_addr4 = self.nodes[0].gettransaction(self.issuance_txid4)['details'][0]['address']
        self.nodes[1].importaddress(self.issuance_addr4)

        issuance_key1 = self.nodes[0].dumpissuanceblindingkey(self.issuance_txid1, self.issuance_vin1)
        self.nodes[1].importissuanceblindingkey(self.issuance_txid1, self.issuance_vin1, issuance_key1)
        issuance_key2 = self.nodes[0].dumpissuanceblindingkey(self.issuance_txid2, self.issuance_vin2)
        self.nodes[1].importissuanceblindingkey(self.issuance_txid2, self.issuance_vin2, issuance_key2)
        issuance_key3 = self.nodes[0].dumpissuanceblindingkey(self.issuance_txid3, self.issuance_vin3)
        self.nodes[1].importissuanceblindingkey(self.issuance_txid3, self.issuance_vin3, issuance_key3)
        issuance_key4 = self.nodes[0].dumpissuanceblindingkey(self.issuance_txid4, self.issuance_vin4)
        self.nodes[1].importissuanceblindingkey(self.issuance_txid4, self.issuance_vin4, issuance_key4)

        issuances = self.nodes[0].listissuances()
        assert len(issuances) == 6
        issuances = self.nodes[1].listissuances()
        assert len(issuances) == 5

    def send_funds(self, node, address, amount, asset, fee_asset, expected_fee=None):
        tx = node.sendtoaddress(
            address=address,
            amount=amount,
            assetlabel=asset,
            fee_asset_label=fee_asset)

        if expected_fee is not None:
            assert_equal(node.getrawmempool(True)[tx]['fees']['base'], Decimal(expected_fee))

        node.generatetoaddress(1, self.node0_mining_address, invalid_call=False)
        self.sync_all()

        # print(json.dumps(node.getrawtransaction(tx, True), indent=4, sort_keys=True, default=str))

        assert len(node.getrawmempool()) == 0

    def scenario1(self):
        self.send_funds(self.nodes[0], self.node1_address, 2.0, self.asset4, self.asset4, '0.00005140')

        balance = self.nodes[1].getreceivedbyaddress(address=self.node1_address, assetlabel=self.asset4)
        assert balance == Decimal(2.0)

    def scenario2(self):
        self.send_funds(self.nodes[0], self.node1_address, 1.0, self.asset4, self.asset1, '0.00000033')

        balance = self.nodes[1].getreceivedbyaddress(address=self.node1_address, assetlabel=self.asset4)
        assert balance == Decimal(3.0)

    def scenario3(self):
        self.send_funds(self.nodes[0], self.node1_address, 3.0, self.asset1, self.asset1, '0.00000021')

        balance = self.nodes[1].getreceivedbyaddress(address=self.node1_address, assetlabel=self.asset1)
        assert balance == Decimal(3.0)

    def scenario4(self):
        self.send_funds(self.nodes[0], self.node1_address, 4.0, self.asset1, self.asset4, '0.00007840')

        balance = self.nodes[1].getreceivedbyaddress(address=self.node1_address, assetlabel=self.asset1)
        assert balance == Decimal(7.0)

    def scenario5(self):
        self.send_funds(self.nodes[0], self.node1_address, 5.0, self.asset3, self.asset3, '0.00000013')

        balance = self.nodes[1].getreceivedbyaddress(address=self.node1_address, assetlabel=self.asset3)
        assert balance == Decimal(5.0)

    def scenario6(self):
        self.send_funds(self.nodes[0], self.node1_address, 6.0, self.asset3, self.asset2, '0.00000023')

        balance = self.nodes[1].getreceivedbyaddress(address=self.node1_address, assetlabel=self.asset3)
        assert balance == Decimal(11.0)

    def scenario7(self):
        tx = self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=2.0,
            assetlabel=self.asset5,
            fee_asset_label=self.asset5)

        assert len(self.nodes[0].getrawmempool()) == 1

        self.nodes[1].sendrawtransaction(self.nodes[0].getrawtransaction(tx))

        assert len(self.nodes[1].getrawmempool()) == 1

        self.nodes[0].generatetoaddress(1, self.node0_address, invalid_call=False)
        self.sync_all()

        balance = self.nodes[1].getreceivedbyaddress(address=self.node1_address, assetlabel=self.asset5)
        assert balance == Decimal(2.0)

        tx = self.nodes[1].sendtoaddress(
            address=self.node0_address,
            amount=1.0,
            assetlabel=self.asset5,
            fee_asset_label=self.asset5)

        assert len(self.nodes[1].getrawmempool()) == 0

        self.nodes[1].removeprunedfunds(tx)

        assert len(self.nodes[0].getrawmempool()) == 0
        assert len(self.nodes[1].getrawmempool()) == 0

    def scenario8(self):
        new_rates = { "test": 100000000, self.asset1: 23493000000, self.asset2: 33289000000, self.asset3: 38884000000, self.asset4: 99990000, self.asset5: 1000000}
        self.nodes[1].setfeeexchangerates(new_rates)

        tx = self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=1.0,
            assetlabel=self.asset5,
            fee_asset_label=self.asset5)

        assert len(self.nodes[0].getrawmempool()) == 1

        assert_raises_rpc_error(-26, "min relay fee not met,", self.nodes[1].sendrawtransaction, self.nodes[0].getrawtransaction(tx))

        assert len(self.nodes[1].getrawmempool()) == 0

        self.nodes[0].generatetoaddress(1, self.node0_address, invalid_call=False)
        self.sync_all()

        tx = self.nodes[1].sendtoaddress(
            address=self.node0_address,
            amount=1.0,
            assetlabel=self.asset5,
            fee_asset_label=self.asset5)

        assert len(self.nodes[1].getrawmempool()) == 1

        self.nodes[1].generatetoaddress(1, self.node1_address, invalid_call=False)
        self.sync_all()

        assert len(self.nodes[0].getrawmempool()) == 0
        assert len(self.nodes[1].getrawmempool()) == 0

    def scenario9(self):
        tx = self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=1.0,
            assetlabel=self.asset2,
            fee_asset_label=self.asset2)

        self.nodes[1].sendrawtransaction(self.nodes[0].getrawtransaction(tx))
        assert len(self.nodes[1].getrawmempool()) == 1

        assert self.nodes[0].getrawmempool(True)[tx]['fees']['base'] == Decimal('0.00000015')
        assert self.nodes[1].getrawmempool(True)[tx]['fees']['base'] == Decimal('0.00000015')

        tx1 = self.nodes[0].bumpfee(tx)['txid']

        self.nodes[1].sendrawtransaction(self.nodes[0].getrawtransaction(tx1))
        assert len(self.nodes[1].getrawmempool()) == 1

        assert self.nodes[0].getrawmempool(True)[tx1]['fees']['base'] == Decimal('0.00000018')
        assert self.nodes[1].getrawmempool(True)[tx1]['fees']['base'] == Decimal('0.00000018')

        self.nodes[0].generatetoaddress(1, self.node0_address, invalid_call=False)
        self.sync_all()

        assert len(self.nodes[0].getrawmempool()) == 0
        assert len(self.nodes[1].getrawmempool()) == 0

    def scenario10(self):
        tx = self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=1.0,
            assetlabel=self.asset2,
            fee_asset_label=self.asset2)

        self.nodes[1].sendrawtransaction(self.nodes[0].getrawtransaction(tx))

        assert self.nodes[0].getrawmempool(True)[tx]['fees']['base'] == Decimal('0.00000015')
        assert self.nodes[1].getrawmempool(True)[tx]['fees']['base'] == Decimal('0.00000015')

        tx1 = self.nodes[0].bumpfee(tx, {'fee_asset': self.asset1})['txid']
        self.nodes[1].sendrawtransaction(self.nodes[0].getrawtransaction(tx1))

        assert self.nodes[0].getrawmempool(True)[tx1]['fees']['asset'] == self.asset1
        assert self.nodes[0].getrawmempool(True)[tx1]['fees']['base'] == Decimal('0.00000033')
        assert self.nodes[1].getrawmempool(True)[tx1]['fees']['asset'] == self.asset1
        assert self.nodes[1].getrawmempool(True)[tx1]['fees']['base'] == Decimal('0.00000033')

        self.nodes[0].generatetoaddress(1, self.node0_address, invalid_call=False)
        self.sync_all()

        assert len(self.nodes[0].getrawmempool()) == 0
        assert len(self.nodes[1].getrawmempool()) == 0

    def run_test(self):
        self.init()

        # Send USDT with paying fees in USDT
        self.scenario1()

        # Send USDT with paying fees in TEST
        self.scenario2()

        # Send AAPL with paying fees in AAPL
        self.scenario3()

        # Send AAPL with paying fees in USDT
        self.scenario4()

        # Send MSTR with paying fees in MSTR
        self.scenario5()

        # Send MSTR with paying fees in TSLA
        self.scenario6()

        # # Send UNKW with paying fees in UNKW, accepted on node0 and accepted on node1 without price set, mined on node0 and synced on node1. Not possible to create the tx on node1 without the price.
        self.scenario7()

        # # Send UNKW with paying fees in UNKW, accepted on node0 and not accepted on node1 with price set lower on node1, mined on node0 and synced on node1, tx created on node1 with more fee accepted
        self.scenario8()

        # Bump fee amount for tx, check that the tx is on node1 after bumping the fee
        self.scenario9()

        # RBF, bumpf fee with changing the asset to pay the fee, check that the tx is on node1 after RBF
        self.scenario10()

if __name__ == '__main__':
    AnyAssetFeeScenariosTest().main()
