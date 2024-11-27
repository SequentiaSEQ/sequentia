#!/usr/bin/env python3
# Copyright (c) 2017-2020 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Tests fees being paid in any asset feature"""

from test_framework.blocktools import COINBASE_MATURITY
from test_framework.test_framework import BitcoinTestFramework
from decimal import Decimal
from test_framework.util import (
    assert_equal,
)
from test_framework.messages import (
    BIP125_SEQUENCE_NUMBER,
)

class AnyAssetFeeTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 2
        self.extra_args = [[
            "-blindedaddresses=0",
            "-initialfreecoins=10000000000",
            "-con_connect_genesis_outputs=1",
            "-con_any_asset_fees=1",
            "-defaultpeggedassetname=gasset",
            "-walletrbf=1",
            "-minrelaytxfee=0.0000001"
        ]] * self.num_nodes
        self.extra_args[0].append("-anyonecanspendaremine=1")

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def init(self):
        self.generate(self.nodes[0], COINBASE_MATURITY + 1)
        self.sync_all()

        self.gasset = self.nodes[0].dumpassetlabels()['gasset']
        self.issue_amount = Decimal('100')
        self.issuance = self.nodes[0].issueasset(self.issue_amount, 1, False)
        self.asset = self.issuance['asset']
        #token = issuance['token']
        self.issuance_txid = self.issuance['txid']
        self.issuance_vin = self.issuance['vin']

        assert len(self.nodes[0].listissuances()) == 2

        self.nodes[0].generatetoaddress(1, self.nodes[0].getnewaddress(), invalid_call=False)  # confirm the tx

        self.issuance_addr = self.nodes[0].gettransaction(self.issuance_txid)['details'][0]['address']
        self.nodes[1].importaddress(self.issuance_addr)

        issuance_key = self.nodes[0].dumpissuanceblindingkey(self.issuance_txid, self.issuance_vin)
        self.nodes[1].importissuanceblindingkey(self.issuance_txid, self.issuance_vin, issuance_key)

        self.issue_amount1 = Decimal('200')
        self.issuance1 = self.nodes[0].issueasset(self.issue_amount1, 1, False)
        self.asset1 = self.issuance1['asset']
        #token = issuance['token']
        self.issuance_txid1 = self.issuance1['txid']
        self.issuance_vin1 = self.issuance1['vin']

        assert len(self.nodes[0].listissuances()) == 3

        self.nodes[0].generatetoaddress(1, self.nodes[0].getnewaddress(), invalid_call=False)  # confirm the tx

        self.node0_address = self.nodes[0].getnewaddress()
        self.node1_address = self.nodes[1].getnewaddress()

        new_rates = { "gasset": 1000000000, self.asset: 100000000,  self.asset1: 1000000000 }
        self.nodes[0].setfeeexchangerates(new_rates)
        self.nodes[1].setfeeexchangerates(new_rates)

        for _ in range(25):
            self.nodes[0].sendtoaddress(
                address=self.node1_address,
                amount=0.1,
                assetlabel=self.asset,
                fee_asset_label=self.asset)
            self.nodes[0].sendtoaddress(
                address=self.node1_address,
                amount=0.2,
                assetlabel=self.asset1,
                fee_asset_label=self.asset1)
            self.nodes[0].sendtoaddress(
                address=self.node1_address,
                amount=0.01,
                assetlabel='gasset',
                fee_asset_label='gasset')
        self.generatetoaddress(self.nodes[0], 1, self.node0_address)
        self.sync_all()

    def test_bump_fee(self):
        [node0, node1] = self.nodes
        tx_id = self.spend_one_input(node1, self.node0_address, self.asset, self.asset1)
        tx = node1.gettransaction(tx_id, True)
        assert_equal(node1.getrawmempool(), [tx_id])

        assert_equal(tx['details'][0]['fee_asset'], self.asset1)
        bumped_tx = node1.bumpfee(tx_id, {'fee_asset': 'gasset'})
        new_tx_id = bumped_tx['txid']
        old_fee = -tx['fee'][self.asset1]
        new_fee = bumped_tx['fee']

        # First, check that the fee asset has changed
        assert_equal(bumped_tx['fee_asset'], self.gasset)

        # And that the old fee is interpreted correctly
        assert_equal(old_fee, bumped_tx['origfee'])

        # And finally, that the new fee is LESS than the old fee, since it is a more highly valued asset
        # assert new_fee < old_fee

        # Verify that the old transaction is gone and has been replaced by the new one in the mempool
        assert_equal(node1.getrawmempool(), [new_tx_id])

        self.generatetoaddress(node1, 1, self.node1_address)
        self.sync_all()

        new_tx = node1.gettransaction(new_tx_id, True)
        assert_equal(new_tx['confirmations'], 1)
        assert_equal(new_tx['details'][0]['fee'], new_fee)

        tx_id = self.spend_one_input(node1, self.node0_address, self.asset, self.asset)
        tx = node1.gettransaction(tx_id, True)
        assert_equal(node1.getrawmempool(), [tx_id])

        assert_equal(tx['details'][0]['fee_asset'], self.asset)
        bumped_tx = node1.bumpfee(tx_id, {'fee_asset': 'gasset'})
        new_tx_id = bumped_tx['txid']
        old_fee = -tx['fee'][self.asset]
        new_fee = bumped_tx['fee']

        # First, check that the fee asset has changed
        assert_equal(bumped_tx['fee_asset'], self.gasset)

        # And that the old fee is interpreted correctly
        assert_equal(old_fee, bumped_tx['origfee'])

        # And finally, that the new fee is LESS than the old fee, since it is a more highly valued asset
        assert new_fee < old_fee

        # Verify that the old transaction is gone and has been replaced by the new one in the mempool
        assert_equal(node1.getrawmempool(), [new_tx_id])

        self.generatetoaddress(node1, 1, self.node1_address)
        self.sync_all()

        new_tx = node1.gettransaction(new_tx_id, True)
        assert_equal(new_tx['confirmations'], 1)
        assert_equal(new_tx['details'][0]['fee'], new_fee)

    def spend_one_input(self, node, dest_address, asset, fee_asset):
        unspent_input = next(u for u in node.listunspent() if u['asset'] == asset)
        tx_input = dict(sequence=BIP125_SEQUENCE_NUMBER, **unspent_input)
        send_amount = Decimal("0.00050000")
        fee_amount = Decimal("0.00001")
        inputs = [tx_input]
        if asset != fee_asset:
            fee_unspent_input = next(u for u in node.listunspent() if u['asset'] == fee_asset)
            fee_input = dict(sequence=BIP125_SEQUENCE_NUMBER, **fee_unspent_input)
            change_amount = tx_input['amount'] - send_amount
            fee_change_amount = fee_input['amount'] - fee_amount
            assert tx_input['amount'] == change_amount + send_amount
            assert fee_input['amount'] == fee_amount + fee_change_amount
            inputs += [fee_input]
        else:
            change_amount = tx_input['amount'] - send_amount - fee_amount
            assert tx_input['amount'] == change_amount + send_amount + fee_amount
        outputs = [
            {dest_address: send_amount, 'asset': asset},
            {"fee": fee_amount, 'fee_asset': fee_asset},
            {node.getrawchangeaddress(): change_amount, 'asset': asset}]
        if asset != fee_asset:
            outputs += [{node.getrawchangeaddress(): fee_change_amount, 'asset': fee_asset}]
        rawtx = node.createrawtransaction(inputs, outputs)
        signedtx = node.signrawtransactionwithwallet(rawtx)
        txid = node.sendrawtransaction(signedtx["hex"])
        return txid

    def run_test(self):
        self.init()
        self.test_bump_fee()

if __name__ == '__main__':
    AnyAssetFeeTest().main()
