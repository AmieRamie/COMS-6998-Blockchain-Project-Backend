const ReceiptManager = artifacts.require('ReceiptManager');
const {
    time, // time comparison support
    BN, // Big Number support
    expectEvent,
    balance, // Assertions for emitted events
} = require('@openzeppelin/test-helpers');

// `accounts` is an array of available Ethereum addresses provided by Truffle’s test environment
contract('ReceiptManager', (accounts) => {
    const seller = accounts[0];
    const buyer = accounts[1];
    let receiptManager;

    // create a new instance of ReceiptManager before each test
    beforeEach(async () => {
        receiptManager = await ReceiptManager.new(30, { from: seller }); // 30-day return window
    });

    it('should issue a receipt and retrieve it later', async () => {
        const amount = web3.utils.toWei('0.1', 'ether');

        // reference: https://archive.trufflesuite.com/docs/truffle/how-to/contracts/interact-with-your-contracts/#processing-transaction-results
        // result.tx - Transaction hash
        // result.logs - Decoded events (logs)
        // result.receipt - Transaction receipt (includes the amount of gas used)
        const result = await receiptManager.issueReceipt(buyer, {
            from: seller,
            value: amount,
        });
        expectEvent(result, 'ReceiptIssued', {
            buyer: buyer,
            purchaseAmount: amount,
        });

        // Extract receipt index from the transaction receipt
        const receiptIndex = result.logs[0].args.receiptIndex.toNumber();

        // Verify that the receipt was issued
        const receipt = await receiptManager.getReceipt(buyer, receiptIndex);

        assert.equal(
            receipt[0].toString(),
            amount,
            'Purchase amount is incorrect'
        );
        // reference: https://docs.openzeppelin.com/test-helpers/0.5/api#time
        assert(
            (await time.latest()).gte(receipt[1].toNumber()),
            'Purchase time is incorrect'
        );
        assert.equal(
            receipt[2],
            false,
            'Refund should not be issued initially'
        );
        assert.equal(
            receipt[3],
            false,
            'Funds should not be released initially'
        );
    });

    it('should allow the buyer to request a refund within the return window', async () => {
        const amount = web3.utils.toWei('0.1', 'ether');
        const buyerInitialBalance = await web3.eth.getBalance(buyer);

        // Issue a receipt
        const result = await receiptManager.issueReceipt(buyer, {
            from: seller,
            value: amount,
        });
        const receiptIndex = result.logs[0].args.receiptIndex.toNumber();
        // const gasUsed = result.receipt.gasUsed;

        // Wait for a short time (less than 30 days) to simulate time within the return window
        await time.increase(time.duration.days(10));

        // Request a refund
        const receiptBeforeRefund = await receiptManager.getReceipt(
            buyer,
            receiptIndex
        );
        assert.equal(
            receiptBeforeRefund[2],
            false,
            'Refund should not have been issued yet'
        );

        // Buyer requests a refund
        const receipt = await receiptManager.requestReturn(receiptIndex, {
            from: buyer,
        });

        // Ensure the refund event is emitted
        expectEvent(receipt, 'RefundIssued', {
            buyer: buyer,
            refundAmount: amount,
        });

        // Verify the receipt after the refund
        const receiptAfterRefund = await receiptManager.getReceipt(
            buyer,
            receiptIndex
        );
        assert.equal(
            receiptAfterRefund[2],
            true,
            'Refund should be issued after request'
        );

        const buyerBalanceAfterRefund = await web3.eth.getBalance(buyer);
        const balanceDifference = new BN(buyerBalanceAfterRefund).sub(
            new BN(buyerInitialBalance)
        );
        // Check that the buyer's balance has been refunded
        assert(
            balanceDifference > amount * 0.8,
            'Buyer should have been refunded'
        );
    });

    it('should prevent refund after the return window expires', async () => {
        const amount = web3.utils.toWei('0.1', 'ether');

        // Issue a receipt
        const result = await receiptManager.issueReceipt(buyer, {
            from: seller,
            value: amount,
        });
        const receiptIndex = result.logs[0].args.receiptIndex.toNumber();

        // Wait for the return window to expire (30 days)
        await time.increase(time.duration.days(31));

        try {
            // Buyer tries to request a refund after the return window has passed
            await receiptManager.requestReturn(receiptIndex, { from: buyer });
            assert.fail(
                'Refund should not be allowed after return window has expired'
            );   // should not reach here
        } catch (error) {
            // see the Require statement in ReceiptManager.sol
            assert(
                error.message.includes('Return window has closed'),
                'Expected error for expired return window'
            );
        }
    });


    
});
